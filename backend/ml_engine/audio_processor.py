"""
Audio Processor and Validation Utility for TRANSLARA.

Handles:
- Validation of audio chunk frames
- Resampling & channel conversion to mono 16kHz PCM16
- Normalization and energy level computation
"""
from __future__ import annotations

import io
from typing import Optional, Tuple
import numpy as np
from loguru import logger

TARGET_SAMPLE_RATE = 16000
FRAME_MS = 30
BYTES_PER_SAMPLE = 2  # 16-bit PCM


class AudioProcessor:
    """Utilities for processing incoming real microphone streams."""

    @staticmethod
    def compute_rms(pcm16_bytes: bytes) -> float:
        """Compute Root Mean Square (RMS) energy level of PCM16 audio."""
        if not pcm16_bytes or len(pcm16_bytes) < 2:
            return 0.0
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16)
        if len(samples) == 0:
            return 0.0
        rms = np.sqrt(np.mean(samples.astype(np.float64) ** 2))
        return float(rms)

    @staticmethod
    def normalize_pcm16(pcm16_bytes: bytes, target_peak: float = 0.95) -> bytes:
        """Normalize audio amplitude to target peak to optimize ASR transcription."""
        if not pcm16_bytes:
            return pcm16_bytes
        samples = np.frombuffer(pcm16_bytes, dtype=np.int16).astype(np.float32) / 32768.0
        max_val = np.max(np.abs(samples))
        if max_val > 0:
            samples = (samples / max_val) * target_peak
        int16_samples = np.clip(samples * 32767.0, -32768, 32767).astype(np.int16)
        return int16_samples.tobytes()

    @staticmethod
    def validate_pcm16_frame(frame: bytes, expected_length: int = 960) -> bytes:
        """Ensure a 30ms PCM16 frame is exactly expected_length bytes (pads or truncates)."""
        if len(frame) == expected_length:
            return frame
        if len(frame) < expected_length:
            return frame + b"\x00" * (expected_length - len(frame))
        return frame[:expected_length]


def get_audio_processor() -> AudioProcessor:
    return AudioProcessor()
