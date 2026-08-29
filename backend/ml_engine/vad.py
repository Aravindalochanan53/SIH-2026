"""
Real-Time Voice Activity Detection (VAD) for streaming PCM16 16kHz audio.
"""
from __future__ import annotations

import collections
import numpy as np
from loguru import logger

SAMPLE_RATE = 16000
FRAME_MS = 30
FRAME_BYTES = int(SAMPLE_RATE * (FRAME_MS / 1000.0) * 2)  # 960 bytes

try:
    import webrtcvad

    HAS_WEBRTCVAD = True
except ImportError:
    HAS_WEBRTCVAD = False
    webrtcvad = None


class StreamingVAD:
    """
    Streaming Voice Activity Detector that accumulates speech frames and yields
    a complete utterance buffer when tail silence is detected or max duration is reached.
    """

    def __init__(
        self,
        aggressiveness: int = 2,
        tail_silence_ms: int = 260,
        min_utterance_ms: int = 250,
        max_utterance_ms: int = 12000,
        sample_rate: int = SAMPLE_RATE,
        frame_ms: int = FRAME_MS,
    ):
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms
        self.frame_bytes = int(sample_rate * (frame_ms / 1000.0) * 2)
        self.tail_silence_frames = max(1, int(tail_silence_ms / frame_ms))
        self.min_utterance_frames = max(1, int(min_utterance_ms / frame_ms))
        self.max_utterance_frames = max(1, int(max_utterance_ms / frame_ms))

        self.vad = None
        if HAS_WEBRTCVAD:
            try:
                self.vad = webrtcvad.Vad(min(3, max(0, aggressiveness)))
            except Exception as e:
                logger.warning(f"Failed to initialize webrtcvad: {e}. Using energy-based fallback.")
                self.vad = None

        self._buffer: list[bytes] = []
        self._silent_frame_count: int = 0
        self._is_speaking: bool = False
        self._leftover: bytes = b""

    def _is_speech_frame(self, frame: bytes) -> bool:
        """Determines if a 30ms PCM16 frame contains speech."""
        if len(frame) != self.frame_bytes:
            return False

        if self.vad is not None:
            try:
                return self.vad.is_speech(frame, self.sample_rate)
            except Exception:
                pass

        # Energy-based fallback
        try:
            samples = np.frombuffer(frame, dtype=np.int16)
            rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
            return rms > 300.0
        except Exception:
            return False

    def process_frame(self, chunk: bytes) -> bytes | None:
        """
        Processes an incoming audio chunk (or frame).
        Returns complete speech byte buffer if an utterance just concluded, else None.
        """
        data = self._leftover + chunk
        self._leftover = b""

        concluded_utterance = None

        while len(data) >= self.frame_bytes:
            frame = data[: self.frame_bytes]
            data = data[self.frame_bytes :]

            is_speech = self._is_speech_frame(frame)

            if is_speech:
                self._is_speaking = True
                self._silent_frame_count = 0
                self._buffer.append(frame)

                if len(self._buffer) >= self.max_utterance_frames:
                    concluded_utterance = b"".join(self._buffer)
                    self.reset()
                    break
            else:
                if self._is_speaking:
                    self._buffer.append(frame)
                    self._silent_frame_count += 1

                    if self._silent_frame_count >= self.tail_silence_frames:
                        if len(self._buffer) >= self.min_utterance_frames:
                            concluded_utterance = b"".join(self._buffer)
                        self.reset()
                        break

        self._leftover = data
        return concluded_utterance

    def flush(self) -> bytes | None:
        """Flushes any accumulated speech in the buffer."""
        if self._buffer and len(self._buffer) >= self.min_utterance_frames:
            utterance = b"".join(self._buffer)
            self.reset()
            return utterance
        self.reset()
        return None

    def reset(self) -> None:
        """Resets the state tracking for a new utterance."""
        self._buffer = []
        self._silent_frame_count = 0
        self._is_speaking = False
        self._leftover = b""
