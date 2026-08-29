/**
 * TRANSLARA — Audio Processing Utilities.
 */

export function resampleTo16k(audioBuffer, targetSampleRate = 16000) {
  const numChannels = audioBuffer.numberOfChannels;
  const length = audioBuffer.length * targetSampleRate / audioBuffer.sampleRate;
  const offlineCtx = new OfflineAudioContext(numChannels, length, targetSampleRate);
  const bufferSource = offlineCtx.createBufferSource();
  bufferSource.buffer = audioBuffer;
  bufferSource.connect(offlineCtx.destination);
  bufferSource.start(0);
  return offlineCtx.startRendering();
}
