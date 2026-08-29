import { useState, useCallback, useRef } from 'react';

export function useMicrophone({ onAudioFrame, sampleRate = 16000 } = {}) {
  const [isRecording, setIsRecording] = useState(false);
  const [error, setError] = useState(null);
  const streamRef = useRef(null);
  const audioContextRef = useRef(null);

  const start = useCallback(async () => {
    try {
      setError(null);
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: sampleRate,
          echoCancellation: true,
          noiseSuppression: true,
        },
      });
      streamRef.current = stream;
      setIsRecording(true);
    } catch (err) {
      setError(err.message || 'Microphone access denied');
      setIsRecording(false);
    }
  }, [sampleRate]);

  const stop = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
    setIsRecording(false);
  }, []);

  return { isRecording, error, start, stop };
}
