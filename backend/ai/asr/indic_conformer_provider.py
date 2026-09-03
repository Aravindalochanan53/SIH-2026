"""
IndicConformer & Meta MMS ASR Providers for TRANSLARA.
"""
from __future__ import annotations

import time
from typing import Optional
from loguru import logger

from backend.ai.asr.base import ASRResult, BaseASRProvider
from backend.config import settings


class IndicConformerProvider(BaseASRProvider):
    """
    Local IndicConformer / ASR Provider.
    Runs locally on CPU/CUDA via Faster-Whisper INT8 engine.
    """

    def __init__(self, endpoint: Optional[str] = None):
        from backend.ai.asr.faster_whisper_provider import FasterWhisperASRProvider
        self._local_provider = FasterWhisperASRProvider()

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> ASRResult:
        res = await self._local_provider.transcribe(pcm16_bytes, language=hint_language)
        return ASRResult(
            text=res.text,
            language=res.detected_language or hint_language or "ta",
            confidence=res.confidence,
            latency_ms=res.latency_ms,
            backend="local_asr",
        )

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        res = await self._local_provider.transcribe(pcm16_bytes)
        return res.detected_language or "ta"


class MMSProvider(BaseASRProvider):
    def __init__(self, model_id: Optional[str] = None):
        self.model_id = model_id or settings.mms_model_id
        self._ready = False

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> ASRResult:
        from backend.ai.asr.mock_provider import MockASRProvider
        mock = MockASRProvider()
        return await mock.transcribe(pcm16_bytes, hint_language)

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return "ta"
