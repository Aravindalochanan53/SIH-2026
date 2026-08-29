/**
 * TRANSLARA — Extension Popup Controller.
 */

const WS_URL = 'ws://localhost:8000/ws/live-stream';

let isStreaming = false;
let ws = null;
let audioContext = null;
let mediaStream = null;
let scriptProcessor = null;
let playbackContext = null;
let audioQueue = [];
let isPlaying = false;

// DOM Elements
const statusBadge = document.getElementById('status-badge');
const sourceLangSelect = document.getElementById('source-lang');
const targetLangSelect = document.getElementById('target-lang');
const swapBtn = document.getElementById('swap-btn');
const toggleBtn = document.getElementById('toggle-stream-btn');
const btnText = document.getElementById('btn-text');
const transcriptText = document.getElementById('transcript-text');
const translationText = document.getElementById('translation-text');
const latencyVal = document.getElementById('latency-val');

// Load languages dynamically from TRANSLARA registry
async function loadLanguages() {
  try {
    const res = await fetch('http://localhost:8000/api/languages');
    if (res.ok) {
      const data = await res.json();
      if (data.grouped) {
        populateSelect(sourceLangSelect, data.grouped, 'ta');
        populateSelect(targetLangSelect, data.grouped, 'ml');
      }
    }
  } catch (e) {
    console.log('Using default language options');
  }
}

function populateSelect(selectEl, grouped, defaultVal) {
  selectEl.innerHTML = '';
  for (const [region, items] of Object.entries(grouped)) {
    const optgroup = document.createElement('optgroup');
    optgroup.label = region;
    for (const item of items) {
      const opt = document.createElement('option');
      opt.value = item.code;
      opt.textContent = `${item.name} (${item.native_name})`;
      if (item.code === defaultVal) opt.selected = true;
      optgroup.appendChild(opt);
    }
    selectEl.appendChild(optgroup);
  }
}

loadLanguages();

// Swap Languages
swapBtn.addEventListener('click', () => {
  const s = sourceLangSelect.value;
  const t = targetLangSelect.value;
  sourceLangSelect.value = t;
  targetLangSelect.value = s;
});

// Toggle Streaming
toggleBtn.addEventListener('click', async () => {
  if (isStreaming) {
    stopStreaming();
  } else {
    await startStreaming();
  }
});

async function startStreaming() {
  const sourceLang = sourceLangSelect.value;
  const targetLang = targetLangSelect.value;

  updateStatus('connecting', 'Connecting...');

  try {
    ws = new WebSocket(WS_URL);
    ws.binaryType = 'arraybuffer';

    ws.onopen = async () => {
      updateStatus('live', 'Live Streaming');
      isStreaming = true;
      toggleBtn.className = 'primary-btn stop';
      btnText.textContent = 'Stop Translation';

      ws.send(
        JSON.stringify({
          type: 'start',
          source_lang: sourceLang,
          target_lang: targetLang,
          sample_rate: 16000,
        })
      );

      await startAudioCapture();
    };

    ws.onmessage = (e) => {
      if (typeof e.data === 'string') {
        const msg = JSON.parse(e.data);
        if (msg.type === 'translation') {
          transcriptText.textContent = msg.transcript;
          transcriptText.classList.remove('placeholder');
          translationText.textContent = msg.translation;
          translationText.classList.remove('placeholder');
          latencyVal.textContent = `${Math.round(msg.latency_ms || 0)} ms`;

          // Notify active tab HUD
          chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0]?.id) {
              chrome.tabs.sendMessage(tabs[0].id, {
                action: 'UPDATE_TRANSLARA_SUBTITLE',
                data: msg,
              }).catch(() => {});
            }
          });
        } else if (msg.type === 'audio_chunk') {
          enqueueAudioChunk(msg.data);
        }
      }
    };

    ws.onerror = () => {
      updateStatus('error', 'WS Error');
      stopStreaming();
    };

    ws.onclose = () => {
      updateStatus('idle', 'Idle');
      stopStreaming();
    };
  } catch (err) {
    console.error(err);
    updateStatus('error', 'Mic Error');
    stopStreaming();
  }
}

async function startAudioCapture() {
  mediaStream = await navigator.mediaDevices.getUserMedia({
    audio: { channelCount: 1, sampleRate: 16000, noiseSuppression: true },
    video: false,
  });

  const AudioCtx = window.AudioContext || window.webkitAudioContext;
  audioContext = new AudioCtx({ sampleRate: 16000 });

  const source = audioContext.createMediaStreamSource(mediaStream);
  scriptProcessor = audioContext.createScriptProcessor(2048, 1, 1);

  scriptProcessor.onaudioprocess = (e) => {
    if (!isStreaming) return;
    const f32 = e.inputBuffer.getChannelData(0);
    const pcm16 = floatToPCM16(f32);
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(pcm16);
    }
  };

  source.connect(scriptProcessor);
  scriptProcessor.connect(audioContext.destination);
}

function floatToPCM16(f32Array) {
  const buffer = new ArrayBuffer(f32Array.length * 2);
  const view = new DataView(buffer);
  for (let i = 0; i < f32Array.length; i++) {
    const s = Math.max(-1, Math.min(1, f32Array[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buffer;
}

function enqueueAudioChunk(b64) {
  const raw = atob(b64);
  const bytes = new Uint8Array(raw.length);
  for (let i = 0; i < raw.length; i++) bytes[i] = raw.charCodeAt(i);
  const i16 = new Int16Array(bytes.buffer);
  const f32 = new Float32Array(i16.length);
  for (let i = 0; i < i16.length; i++) f32[i] = i16[i] / 32768.0;

  audioQueue.push(f32);
  if (!isPlaying) playNextChunk();
}

function playNextChunk() {
  if (audioQueue.length === 0) {
    isPlaying = false;
    return;
  }
  isPlaying = true;
  const chunk = audioQueue.shift();
  if (!playbackContext || playbackContext.state === 'closed') {
    playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
  }
  const buffer = playbackContext.createBuffer(1, chunk.length, 16000);
  buffer.getChannelData(0).set(chunk);
  const src = playbackContext.createBufferSource();
  src.buffer = buffer;
  src.connect(playbackContext.destination);
  src.onended = () => playNextChunk();
  src.start();
}

function stopStreaming() {
  isStreaming = false;
  toggleBtn.className = 'primary-btn start';
  btnText.textContent = 'Start Translation';

  if (scriptProcessor) {
    scriptProcessor.disconnect();
    scriptProcessor = null;
  }
  if (mediaStream) {
    mediaStream.getTracks().forEach((t) => t.stop());
    mediaStream = null;
  }
  if (audioContext && audioContext.state !== 'closed') {
    audioContext.close();
    audioContext = null;
  }
  if (ws) {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'stop' }));
      ws.close();
    }
    ws = null;
  }
  updateStatus('idle', 'Idle');
}

function updateStatus(state, label) {
  statusBadge.className = `badge ${state}`;
  statusBadge.textContent = label;
}
