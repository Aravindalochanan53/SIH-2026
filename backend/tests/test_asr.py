"""
Unit tests for TRANSLARA ASR Layer.
"""
import pytest
from backend.ml_engine.asr import MockASR, get_asr_backend


@pytest.mark.asyncio
async def test_mock_asr_tamil_transcription():
    asr = MockASR()
    pcm_dummy = b"\x00" * 32000

    transcript = await asr.transcribe(pcm_dummy, hint_language="ta")
    assert transcript.text is not None
    assert len(transcript.text) > 0
    assert transcript.language == "ta"
    assert transcript.confidence > 0.8


@pytest.mark.asyncio
async def test_mock_asr_malayalam_transcription():
    asr = MockASR()
    pcm_dummy = b"\x00" * 32000

    transcript = await asr.transcribe(pcm_dummy, hint_language="ml")
    assert transcript.text is not None
    assert transcript.language == "ml"


def test_asr_singleton():
    b1 = get_asr_backend()
    b2 = get_asr_backend()
    assert b1 is b2
