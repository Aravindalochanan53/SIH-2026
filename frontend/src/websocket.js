/**
 * TRANSLARA — Web Audio & WebSocket Streaming Bridge.
 */

export class StreamingAudioBridge {
  constructor({ onTranslation, onStatusChange, onError }) {
    this.onTranslation = onTranslation;
    this.onStatusChange = onStatusChange;
    this.onError = onError;

    this.ws = null;
    this.audioContext = null;
    this.mediaStream = null;
    this.sourceNode = null;
    this.scriptNode = null;

    this.isStreaming = false;
    this.audioQueue = [];
    this.isPlaying = false;
    this.playbackContext = null;

    const baseWs = import.meta.env.VITE_WS_BASE_URL || 'ws://localhost:8000';
    this.wsUrl = `${baseWs}/ws/live-stream`;
  }

  async start({ sourceLang = 'ta', targetLang = 'ml' }) {
    if (this.isStreaming) return;

    this.onStatusChange?.('connecting');

    try {
      // 1. Establish WebSocket Connection
      this.ws = new WebSocket(this.wsUrl);
      this.ws.binaryType = 'arraybuffer';

      this.ws.onopen = async () => {
        this.onStatusChange?.('listening');
        this.isStreaming = true;

        // Send Start Session Handshake
        this.ws.send(
          JSON.stringify({
            type: 'start',
            source_lang: sourceLang,
            target_lang: targetLang,
            sample_rate: 16000,
          })
        );

        // 2. Start Microphone Audio Capture
        await this._startMicCapture();
      };

      this.ws.onmessage = (event) => {
        if (typeof event.data === 'string') {
          const msg = JSON.parse(event.data);
          if (msg.type === 'translation') {
            this.onTranslation?.(msg);
          } else if (msg.type === 'audio_chunk') {
            this._enqueueAudioChunk(msg.data);
          } else if (msg.type === 'error') {
            this.onError?.(msg.message);
          }
        }
      };

      this.ws.onerror = (err) => {
        console.error('[WS error]', err);
        this.onStatusChange?.('error');
        this.onError?.('WebSocket connection error');
        this.stop();
      };

      this.ws.onclose = () => {
        this.onStatusChange?.('disconnected');
        this.isStreaming = false;
      };
    } catch (err) {
      console.error('[AudioBridge Start Error]', err);
      this.onStatusChange?.('error');
      this.onError?.(err.message || 'Microphone access denied');
      this.stop();
    }
  }

  async _startMicCapture() {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    });

    const AudioContextClass = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioContextClass({ sampleRate: 16000 });

    this.sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.scriptNode = this.audioContext.createScriptProcessor(2048, 1, 1);

    this.scriptNode.onaudioprocess = (e) => {
      if (!this.isStreaming) return;
      const float32 = e.inputBuffer.getChannelData(0);
      const pcm16 = this._floatToPCM16(float32);
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(pcm16);
      }
    };

    this.sourceNode.connect(this.scriptNode);
    this.scriptNode.connect(this.audioContext.destination);
  }

  _floatToPCM16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
  }

  _enqueueAudioChunk(base64Data) {
    const binary = atob(base64Data);
    const bytes = new Uint8Array(binary.length);
    for (let i = 0; i < binary.length; i++) {
      bytes[i] = binary.charCodeAt(i);
    }
    const int16 = new Int16Array(bytes.buffer);
    const float32 = new Float32Array(int16.length);
    for (let i = 0; i < int16.length; i++) {
      float32[i] = int16[i] / 32768.0;
    }
    this.audioQueue.push(float32);
    if (!this.isPlaying) {
      this._playNextChunk();
    }
  }

  _playNextChunk() {
    if (this.audioQueue.length === 0) {
      this.isPlaying = false;
      return;
    }
    this.isPlaying = true;
    const chunk = this.audioQueue.shift();

    if (!this.playbackContext || this.playbackContext.state === 'closed') {
      this.playbackContext = new (window.AudioContext || window.webkitAudioContext)({ sampleRate: 16000 });
    }

    const buffer = this.playbackContext.createBuffer(1, chunk.length, 16000);
    buffer.getChannelData(0).set(chunk);

    const source = this.playbackContext.createBufferSource();
    source.buffer = buffer;
    source.connect(this.playbackContext.destination);
    source.onended = () => {
      this._playNextChunk();
    };
    source.start();
  }

  stop() {
    this.isStreaming = false;

    if (this.scriptNode) {
      this.scriptNode.disconnect();
      this.scriptNode = null;
    }
    if (this.sourceNode) {
      this.sourceNode.disconnect();
      this.sourceNode = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((track) => track.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
    if (this.ws) {
      if (this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({ type: 'stop' }));
        this.ws.close();
      }
      this.ws = null;
    }

    this.onStatusChange?.('stopped');
  }
}
