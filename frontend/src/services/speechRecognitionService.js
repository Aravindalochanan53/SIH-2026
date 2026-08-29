export class SpeechRecognitionService {
  constructor({ onResult, onError } = {}) {
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    this.recognition = SpeechRecognition ? new SpeechRecognition() : null;
    if (this.recognition) {
      this.recognition.continuous = true;
      this.recognition.interimResults = true;
      this.recognition.onresult = (event) => {
        const transcript = Array.from(event.results)
          .map((r) => r[0].transcript)
          .join('');
        onResult?.(transcript);
      };
      this.recognition.onerror = (e) => onError?.(e);
    }
  }

  start(lang = 'ta-IN') {
    if (this.recognition) {
      this.recognition.lang = lang;
      this.recognition.start();
    }
  }

  stop() {
    if (this.recognition) {
      this.recognition.stop();
    }
  }
}
