"""
Unit tests for TRANSLARA Audio Processor and Real Microphone Stream Handler.
"""
import numpy as np
from backend.ml_engine.audio_processor import AudioProcessor


def test_compute_rms_silence():
    processor = AudioProcessor()
    silence = b"\x00" * 960
    rms = processor.compute_rms(silence)
    assert rms == 0.0


def test_compute_rms_speech():
    processor = AudioProcessor()
    # Generate 440 Hz sine wave tone in int16
    t = np.linspace(0, 0.03, 480, endpoint=False)
    sine = (np.sin(2 * np.pi * 440 * t) * 15000).astype(np.int16)
    audio_bytes = sine.tobytes()

    rms = processor.compute_rms(audio_bytes)
    assert rms > 5000.0


def test_normalize_pcm16():
    processor = AudioProcessor()
    # Create low amplitude audio
    low_amp = (np.ones(480, dtype=np.int16) * 1000).tobytes()
    normalized = processor.normalize_pcm16(low_amp, target_peak=0.95)

    samples = np.frombuffer(normalized, dtype=np.int16)
    max_val = np.max(np.abs(samples))
    assert max_val > 25000


def test_validate_pcm16_frame():
    processor = AudioProcessor()
    # Short frame
    short_frame = b"\x01" * 500
    padded = processor.validate_pcm16_frame(short_frame, expected_length=960)
    assert len(padded) == 960

    # Long frame
    long_frame = b"\x01" * 1200
    truncated = processor.validate_pcm16_frame(long_frame, expected_length=960)
    assert len(truncated) == 960
