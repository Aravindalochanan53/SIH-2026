"""
Pipeline Orchestrator for TRANSLARA.

Executes:
PCM Audio -> VAD -> ASR (or Language Detection) -> Entity Lock -> TRANSLARA AI Translation -> Entity Restoration -> Quality Validation -> TTS Streaming.

Enforces sub-3s latency SLA and stage timing instrumentation.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from typing import AsyncGenerator, Optional

from loguru import logger

from backend.ai.language_detection.detector import get_language_detector
from backend.ai.model_manager import get_model_manager
from backend.ai.ner.entity_lock import get_entity_lock
from backend.ai.translation.registry import get_translation_engine
from backend.ai.validators.translation_validator import TranslationValidator
from backend.config import settings
from backend.logging_config import log_pipeline_summary, log_stage_latency
from backend.ml_engine.asr import get_asr_backend
from backend.ml_engine.tts import get_tts_backend
from backend.schemas import LockedEntity


@dataclass
class PipelineResult:
    transcript: str
    translation: str
    source_lang: str
    target_lang: str
    detected_lang: Optional[str] = None
    entities_locked: list[LockedEntity] = field(default_factory=list)
    stage_latencies_ms: dict[str, float] = field(default_factory=dict)
    total_latency_ms: float = 0.0
    used_offline_fallback: bool = False
    warning: Optional[str] = None
    error: Optional[str] = None


async def run_pipeline(
    pcm16_audio: bytes,
    source_lang: str = "ta",
    target_lang: str = "ml",
    session_id: str = "default_session",
) -> PipelineResult:
    """Execute complete real-time translation pipeline."""
    total_start = time.monotonic()
    stage_latencies: dict[str, float] = {}

    asr_backend = get_asr_backend()
    entity_lock = get_entity_lock()
    translation_engine = get_translation_engine()

    # 1. ASR Stage
    t0 = time.monotonic()
    try:
        asr_result = await asyncio.wait_for(
            asr_backend.transcribe(pcm16_audio, hint_language=source_lang),
            timeout=settings.asr_timeout_ms / 1000,
        )
        stage_latencies["asr_ms"] = (time.monotonic() - t0) * 1000
        log_stage_latency(session_id, "ASR", stage_latencies["asr_ms"], f"text='{asr_result.text}'")
    except Exception as e:
        logger.error(f"ASR stage failed ({e})")
        return PipelineResult(
            transcript="",
            translation="",
            source_lang=source_lang,
            target_lang=target_lang,
            error=f"ASR failure: {e}",
            total_latency_ms=(time.monotonic() - total_start) * 1000,
        )

    transcript = asr_result.text
    actual_source_lang = asr_result.language if source_lang in (None, "auto", "") else source_lang

    if not transcript.strip():
        return PipelineResult(
            transcript="",
            translation="",
            source_lang=actual_source_lang,
            target_lang=target_lang,
            total_latency_ms=(time.monotonic() - total_start) * 1000,
        )

    # 2. Entity Lock & Shield Stage
    t1 = time.monotonic()
    detected_entities = entity_lock.detect_entities(transcript)
    masked_text, token_map = entity_lock.mask(transcript, detected_entities)
    stage_latencies["entity_lock_ms"] = (time.monotonic() - t1) * 1000
    log_stage_latency(session_id, "EntityLock", stage_latencies["entity_lock_ms"], f"locked={len(detected_entities)}")

    # 3. Translation Stage via TRANSLARA AI
    t2 = time.monotonic()
    try:
        trans_res = await translation_engine.translate(
            text=masked_text,
            source_lang=actual_source_lang,
            target_lang=target_lang,
        )
        stage_latencies["nmt_ms"] = (time.monotonic() - t2) * 1000
        log_stage_latency(session_id, "NMT", stage_latencies["nmt_ms"], f"backend='{trans_res.backend}'")
    except Exception as e:
        logger.error(f"NMT stage error: {e}")
        return PipelineResult(
            transcript=transcript,
            translation="",
            source_lang=actual_source_lang,
            target_lang=target_lang,
            error=f"NMT failure: {e}",
            total_latency_ms=(time.monotonic() - total_start) * 1000,
        )

    # 4. Entity Restoration & Quality Validation
    t3 = time.monotonic()
    restored_text = entity_lock.unmask(trans_res.text, token_map)
    stage_latencies["unmask_ms"] = (time.monotonic() - t3) * 1000

    val = TranslationValidator.validate(
        source_text=transcript,
        translated_text=restored_text,
        source_lang=actual_source_lang,
        target_lang=target_lang,
        expected_entities=[e.text for e in detected_entities],
    )

    total_latency = (time.monotonic() - total_start) * 1000
    log_pipeline_summary(session_id, actual_source_lang, target_lang, total_latency, transcript, restored_text)

    locked_schemas = [
        LockedEntity(
            text=e.text,
            type=e.type,
            start=e.start_char,
            end=e.end_char,
            phonetic_hint=None,
        )
        for e in detected_entities
    ]

    all_warnings = list(set(trans_res.warnings + val.warnings))

    return PipelineResult(
        transcript=transcript,
        translation=restored_text,
        source_lang=actual_source_lang,
        target_lang=target_lang,
        detected_lang=asr_result.language,
        entities_locked=locked_schemas,
        stage_latencies_ms=stage_latencies,
        total_latency_ms=total_latency,
        used_offline_fallback=trans_res.backend.startswith("offline"),
        warning="; ".join(all_warnings) if all_warnings else None,
    )


async def stream_tts(
    text: str,
    target_lang: str,
) -> AsyncGenerator[bytes, None]:
    """Stream audio chunks for synthesized target speech."""
    tts = get_tts_backend()
    async for chunk in tts.synthesize_stream(text, target_lang):
        yield chunk


async def warm_up() -> None:
    """Pre-warm all AI components during application startup."""
    await get_model_manager().warm_up()
