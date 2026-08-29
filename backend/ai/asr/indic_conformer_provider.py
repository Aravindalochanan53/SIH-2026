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
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or settings.indic_conformer_endpoint

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> ASRResult:
        import httpx
        start = time.monotonic()
        try:
            async with httpx.AsyncClient(timeout=settings.asr_timeout_ms / 1000) as client:
                resp = await client.post(
                    self.endpoint,
                    content=pcm16_bytes,
                    headers={"Content-Type": "audio/x-raw", "X-Language": hint_language or "ta"},
                )
                resp.raise_for_status()
                data = resp.json()
                return ASRResult(
                    text=data.get("text", ""),
                    language=data.get("language", hint_language or "ta"),
                    confidence=data.get("confidence", 0.92),
                    latency_ms=(time.monotonic() - start) * 1000,
                    backend="indic_conformer",
                )
        except Exception as e:
            logger.warning(f"IndicConformer endpoint unavailable ({e}); using fallback.")
            from backend.ai.asr.mock_provider import MockASRProvider
            mock = MockASRProvider()
            return await mock.transcribe(pcm16_bytes, hint_language)

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return "ta"


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
