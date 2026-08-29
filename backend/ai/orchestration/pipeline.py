"""
End-to-End Real-Time Speech-to-Speech & Speech-to-Text Pipeline Orchestrator.
Maintains sub-3-second end-to-end latency budget.
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import AsyncGenerator, Dict, List, Optional
from loguru import logger

from backend.ai.asr.faster_whisper_provider import FasterWhisperProvider
from backend.ai.language_detection.detector import get_language_detector
from backend.ai.ner.entity_lock import get_entity_lock
from backend.ai.translation.registry import get_translation_engine
from backend.ai.tts.indic_tts_provider import IndicTTSProvider
from backend.ai.validators.translation_validator import TranslationValidator


@dataclass
class PipelineResult:
    source_text: str
    translated_text: str
    source_lang: str
    target_lang: str
    detected_lang: str
    entities: List[Dict[str, str]]
    total_latency_ms: float
    stage_latencies: Dict[str, float]
    is_valid: bool
    warnings: List[str]


class RealtimePipeline:
    def __init__(self):
        self.asr = FasterWhisperProvider()
        self.lid = get_language_detector()
        self.entity_lock = get_entity_lock()
        self.translator = get_translation_engine()
        self.tts = IndicTTSProvider()

    async def process_utterance(
        self,
        pcm16_bytes: bytes,
        source_lang: str = "ta",
        target_lang: str = "ml",
    ) -> PipelineResult:
        total_start = time.monotonic()
        stage_latencies: Dict[str, float] = {}

        # 1. ASR Stage
        asr_start = time.monotonic()
        asr_res = await self.asr.transcribe(pcm16_bytes, hint_language=source_lang)
        stage_latencies["asr_ms"] = (time.monotonic() - asr_start) * 1000

        # 2. Language Detection Stage
        detected = self.lid.detect_text(asr_res.text)
        detected_lang = detected.get("language", source_lang)

        # 3. Entity Lock Stage
        lock_start = time.monotonic()
        entities = self.entity_lock.detect_entities(asr_res.text)
        masked_text, token_map = self.entity_lock.mask(asr_res.text, entities)
        stage_latencies["entity_lock_ms"] = (time.monotonic() - lock_start) * 1000

        # 4. Translation Stage
        nmt_start = time.monotonic()
        trans_res = await self.translator.translate(
            masked_text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
        stage_latencies["nmt_ms"] = (time.monotonic() - nmt_start) * 1000

        # 5. Entity Restore & Validation
        unmask_start = time.monotonic()
        restored = self.entity_lock.unmask(trans_res.text, token_map)
        stage_latencies["unmask_ms"] = (time.monotonic() - unmask_start) * 1000

        val = TranslationValidator.validate(
            source_text=asr_res.text,
            translated_text=restored,
            source_lang=source_lang,
            target_lang=target_lang,
            expected_entities=[e.text for e in entities],
        )

        total_latency = (time.monotonic() - total_start) * 1000

        return PipelineResult(
            source_text=asr_res.text,
            translated_text=restored,
            source_lang=source_lang,
            target_lang=target_lang,
            detected_lang=detected_lang,
            entities=[{"text": e.text, "type": e.type} for e in entities],
            total_latency_ms=total_latency,
            stage_latencies=stage_latencies,
            is_valid=val.is_valid,
            warnings=list(set(trans_res.warnings + val.warnings)),
        )

    async def stream_speech_translation(
        self,
        text_to_speak: str,
        target_lang: str,
    ) -> AsyncGenerator[bytes, None]:
        async for audio_chunk in self.tts.synthesize_stream(text_to_speak, target_lang):
            yield audio_chunk


_pipeline_instance: Optional[RealtimePipeline] = None


def get_realtime_pipeline() -> RealtimePipeline:
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = RealtimePipeline()
    return _pipeline_instance
