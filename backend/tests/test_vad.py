"""
Unit tests for Voice Activity Detection (VAD).
"""
import numpy as np
import pytest
from backend.ml_engine.vad import FRAME_BYTES, StreamingVAD


def test_vad_silence_rejection():
    vad = StreamingVAD()
    # Feed pure silence (all zeros)
    silence_frame = b"\x00" * FRAME_BYTES
    for _ in range(10):
        result = vad.process_frame(silence_frame)
        assert result is None


def test_vad_speech_accumulation_and_cutoff():
    vad = StreamingVAD(tail_silence_ms=60, min_utterance_ms=50)

    # Synthetic tone (speech simulation)
    t = np.linspace(0, 0.03, 480, endpoint=False)
    speech_signal = (np.sin(2 * np.pi * 300 * t) * 15000).astype(np.int16).tobytes()
    silence_frame = b"\x00" * FRAME_BYTES

    # 1. Send speech frames (6 frames = 180ms)
    for _ in range(6):
        vad.process_frame(speech_signal)

    # 2. Send silence frames (3 frames = 90ms > tail_silence_ms)
    res = None
    for _ in range(4):
        out = vad.process_frame(silence_frame)
        if out is not None:
            res = out
            break

    assert res is not None
    assert len(res) > 0


def test_vad_flush():
    vad = StreamingVAD(min_utterance_ms=50)
    t = np.linspace(0, 0.03, 480, endpoint=False)
    speech_signal = (np.sin(2 * np.pi * 300 * t) * 15000).astype(np.int16).tobytes()

    for _ in range(5):
        vad.process_frame(speech_signal)

    flushed = vad.flush()
    assert flushed is not None
    assert len(flushed) > 0
