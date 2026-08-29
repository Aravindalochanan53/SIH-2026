"""
Government of India Bhashini ULCA NMT API Provider for TRANSLARA.
"""
from __future__ import annotations

import time
from typing import Optional
import httpx
from loguru import logger

from backend.ai.translation.base import BaseTranslationProvider, TranslationResult
from backend.config import settings


class BhashiniProvider(BaseTranslationProvider):
    def __init__(self):
        self.api_url = settings.bhashini_api_url
        self.user_id = settings.bhashini_user_id
        self.inference_key = settings.bhashini_inference_api_key
        self.pipeline_id = settings.bhashini_pipeline_id
        self._is_configured = bool(self.inference_key and self.user_id)

    def is_pair_supported(self, source_lang: str, target_lang: str) -> bool:
        # Bhashini supports all 22 scheduled Indian languages + English
        supported = {"en", "ta", "te", "kn", "ml", "hi", "bn", "mr", "gu", "or", "pa", "as", "ur"}
        return source_lang.lower() in supported and target_lang.lower() in supported

    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        if not self._is_configured:
            from backend.ai.translation.offline_provider import OfflineTranslationProvider
            offline = OfflineTranslationProvider()
            return await offline.translate(text, source_lang, target_lang)

        start = time.monotonic()
        payload = {
            "pipelineTasks": [
                {
                    "taskType": "translation",
                    "config": {
                        "language": {
                            "sourceLanguage": source_lang.lower(),
                            "targetLanguage": target_lang.lower(),
                        }
                    },
                }
            ],
            "inputData": {
                "input": [{"source": text}]
            },
        }

        headers = {
            "User-Id": self.user_id,
            "Ulca-Api-Key": settings.bhashini_ulca_api_key or self.inference_key,
            "Authorization": self.inference_key,
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.nmt_timeout_ms / 1000) as client:
                resp = await client.post(self.api_url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                translated = data["pipelineResponse"][0]["output"][0]["target"]
                latency_ms = (time.monotonic() - start) * 1000
                return TranslationResult(
                    text=translated,
                    source_lang=source_lang,
                    target_lang=target_lang,
                    latency_ms=latency_ms,
                    backend="bhashini_ulca",
                    confidence=0.95,
                )
        except Exception as e:
            logger.warning(f"Bhashini API error ({e}); falling back to offline provider.")
            from backend.ai.translation.offline_provider import OfflineTranslationProvider
            offline = OfflineTranslationProvider()
            return await offline.translate(text, source_lang, target_lang)
