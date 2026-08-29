"""
Integration tests for TRANSLARA Pipeline Orchestration.
"""
import pytest
from backend.ml_engine.pipeline import run_pipeline, stream_tts


@pytest.mark.asyncio
async def test_end_to_end_south_indian_pipeline():
    """Test full pipeline on Tamil -> Malayalam."""
    dummy_audio = b"\x00" * 32000  # 1 sec

    res = await run_pipeline(
        pcm16_audio=dummy_audio,
        source_lang="ta",
        target_lang="ml",
    )

    assert res.transcript != ""
    assert res.translation != ""
    assert res.source_lang == "ta"
    assert res.target_lang == "ml"
    assert res.total_latency_ms < 3000  # Sub-3s latency SLA
    assert "asr_ms" in res.stage_latencies_ms
    assert "nmt_ms" in res.stage_latencies_ms


@pytest.mark.asyncio
async def test_tts_chunk_streaming_multilingual():
    """Test chunked TTS generation for South Indian language."""
    chunks = []
    async for chunk in stream_tts("നമസ്കാരം, സുഖമാണോ?", "ml"):
        chunks.append(chunk)
        assert len(chunk) > 0

    assert len(chunks) > 0
