import { StreamingAudioBridge } from '../websocket';

export class LiveTranslationService {
  constructor(options = {}) {
    this.bridge = new StreamingAudioBridge(options);
  }

  async start(config) {
    return this.bridge.start(config);
  }

  stop() {
    return this.bridge.stop();
  }
}
