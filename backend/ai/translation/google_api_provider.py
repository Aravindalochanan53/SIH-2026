"""
Google API Translation Provider for TRANSLARA.
Provides rapid, non-blocking translation with batching, automatic language code normalization,
and seamless fallback for Indian languages and English.
"""
from __future__ import annotations

import asyncio
import json
import time
import urllib.parse
import urllib.request
from typing import Dict, List, Optional
from loguru import logger

from backend.ai.translation.base import BaseTranslationProvider, TranslationResult

# Language code mapping for Google Translate API
GOOGLE_LANG_MAP: Dict[str, str] = {
    "ta": "ta",
    "ml": "ml",
    "te": "te",
    "kn": "kn",
    "hi": "hi",
    "bn": "bn",
    "mr": "mr",
    "gu": "gu",
    "ur": "ur",
    "pa": "pa",
    "or": "or",
    "as": "as",
    "en": "en",
    "auto": "auto",
}


def _translate_single_sync(text: str, source_lang: str, target_lang: str, timeout: float = 10.0) -> str:
    """Synchronous worker function to call Google Translate endpoint."""
    src = GOOGLE_LANG_MAP.get(source_lang.lower().strip(), source_lang)
    tgt = GOOGLE_LANG_MAP.get(target_lang.lower().strip(), target_lang)

    quoted = urllib.parse.quote(text)
    url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src}&tl={tgt}&dt=t&q={quoted}"

    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        },
    )

    with urllib.request.urlopen(req, timeout=timeout) as response:
        raw_body = response.read().decode("utf-8")
        data = json.loads(raw_body)
        # Structure is [[[translated_chunk, source_chunk, ...], ...], ...]
        translated_parts = []
        if isinstance(data, list) and len(data) > 0 and isinstance(data[0], list):
            for part in data[0]:
                if isinstance(part, list) and len(part) > 0 and part[0]:
                    translated_parts.append(str(part[0]))
        return "".join(translated_parts) if translated_parts else text


class GoogleAPIProvider(BaseTranslationProvider):
    """
    High-availability Google API Translation Provider.
    Works asynchronously with thread-pool execution and concurrent batch processing.
    """

    def __init__(self):
        self.backend_name = "google_api"

    async def translate(
        self,
        text: str,
        source_lang: str = "ta",
        target_lang: str = "ml",
    ) -> TranslationResult:
        start_time = time.monotonic()
        cleaned_text = (text or "").strip()
        if not cleaned_text:
            return TranslationResult(
                text="",
                source_lang=source_lang,
                target_lang=target_lang,
                latency_ms=0.0,
                backend=self.backend_name,
                confidence=1.0,
            )

        try:
            loop = asyncio.get_running_loop()
            translated = await loop.run_in_executor(
                None,
                _translate_single_sync,
                cleaned_text,
                source_lang,
                target_lang,
            )
            latency = (time.monotonic() - start_time) * 1000
            return TranslationResult(
                text=translated,
                source_lang=source_lang,
                target_lang=target_lang,
                latency_ms=latency,
                backend=self.backend_name,
                confidence=0.98,
            )
        except Exception as err:
            logger.warning(f"GoogleAPIProvider translation error: {err}")
            latency = (time.monotonic() - start_time) * 1000
            return TranslationResult(
                text=cleaned_text,
                source_lang=source_lang,
                target_lang=target_lang,
                latency_ms=latency,
                backend=self.backend_name,
                confidence=0.0,
                warnings=[f"API error: {err}"],
            )

    async def translate_batch(
        self,
        texts: List[str],
        source_lang: str = "ta",
        target_lang: str = "ml",
        concurrency: int = 10,
    ) -> List[str]:
        """Translate a batch of texts concurrently with a semaphore."""
        sem = asyncio.Semaphore(concurrency)

        async def _worker(t: str) -> str:
            if not t or not t.strip():
                return ""
            async with sem:
                res = await self.translate(t, source_lang, target_lang)
                return res.text

        tasks = [_worker(t) for t in texts]
        return await asyncio.gather(*tasks)


_google_provider_instance: Optional[GoogleAPIProvider] = None


def get_google_provider() -> GoogleAPIProvider:
    global _google_provider_instance
    if _google_provider_instance is None:
        _google_provider_instance = GoogleAPIProvider()
    return _google_provider_instance
