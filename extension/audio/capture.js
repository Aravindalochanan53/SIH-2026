/**
 * TRANSLARA — Audio Capture Engine.
 */

export class AudioCapture {
  constructor({ onAudioData, sampleRate = 16000 }) {
    this.onAudioData = onAudioData;
    this.sampleRate = sampleRate;
    this.audioContext = null;
    this.mediaStream = null;
    this.processor = null;
    this.isRecording = false;
  }

  async startMicrophone() {
    this.mediaStream = await navigator.mediaDevices.getUserMedia({
      audio: {
        channelCount: 1,
        echoCancellation: true,
        noiseSuppression: true,
        autoGainControl: true,
      },
      video: false,
    });
    this._initAudioPipeline();
  }

  async startTabCapture() {
    return new Promise((resolve, reject) => {
      chrome.tabCapture.capture(
        { audio: true, video: false },
        (stream) => {
          if (!stream) {
            return reject(new Error('Tab capture denied or unavailable'));
          }
          this.mediaStream = stream;
          this._initAudioPipeline();
          resolve();
        }
      );
    });
  }

  _initAudioPipeline() {
    const AudioCtx = window.AudioContext || window.webkitAudioContext;
    this.audioContext = new AudioCtx({ sampleRate: this.sampleRate });

    const sourceNode = this.audioContext.createMediaStreamSource(this.mediaStream);
    this.processor = this.audioContext.createScriptProcessor(2048, 1, 1);

    this.processor.onaudioprocess = (e) => {
      if (!this.isRecording) return;
      const inputData = e.inputBuffer.getChannelData(0);
      const pcm16 = this._convertFloat32ToPCM16(inputData);
      this.onAudioData?.(pcm16);
    };

    sourceNode.connect(this.processor);
    this.processor.connect(this.audioContext.destination);
    this.isRecording = true;
  }

  _convertFloat32ToPCM16(float32Array) {
    const buffer = new ArrayBuffer(float32Array.length * 2);
    const view = new DataView(buffer);
    for (let i = 0; i < float32Array.length; i++) {
      const s = Math.max(-1, Math.min(1, float32Array[i]));
      view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
    }
    return buffer;
  }

  stop() {
    this.isRecording = false;
    if (this.processor) {
      this.processor.disconnect();
      this.processor = null;
    }
    if (this.mediaStream) {
      this.mediaStream.getTracks().forEach((t) => t.stop());
      this.mediaStream = null;
    }
    if (this.audioContext && this.audioContext.state !== 'closed') {
      this.audioContext.close();
      this.audioContext = null;
    }
  }
}
