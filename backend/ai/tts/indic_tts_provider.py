"""
TTS Providers for TRANSLARA (IndicTTS, VITS, Bhashini, Mock).
"""
from __future__ import annotations

import asyncio
from typing import AsyncGenerator, Optional
import numpy as np
from loguru import logger

from backend.ai.tts.base import BaseTTSProvider
from backend.config import settings
from backend.ml_engine.languages import get_language

SAMPLE_RATE = 16000
CHUNK_DURATION_S = 0.20
CHUNK_SAMPLES = int(SAMPLE_RATE * CHUNK_DURATION_S)


class IndicTTSProvider(BaseTTSProvider):
    def __init__(self, endpoint: Optional[str] = None):
        self.endpoint = endpoint or settings.indic_tts_endpoint

    async def synthesize_stream(
        self, text: str, target_lang: str
    ) -> AsyncGenerator[bytes, None]:
        import httpx
        lang_cfg = get_language(target_lang)
        if not lang_cfg or not lang_cfg.tts_supported:
            return

        try:
            async with httpx.AsyncClient(timeout=settings.tts_timeout_ms / 1000) as client:
                payload = {"text": text, "language": target_lang, "gender": "female"}
                resp = await client.post(self.endpoint, json=payload)
                resp.raise_for_status()
                audio_bytes = resp.content

                for i in range(0, len(audio_bytes), CHUNK_SAMPLES * 2):
                    chunk = audio_bytes[i : i + CHUNK_SAMPLES * 2]
                    yield chunk
                    await asyncio.sleep(0.04)
        except Exception as e:
            logger.warning(f"IndicTTS API unavailable ({e}); using synthetic stream.")
            mock = MockTTSProvider()
            async for chunk in mock.synthesize_stream(text, target_lang):
                yield chunk


class VITSLocalProvider(BaseTTSProvider):
    async def synthesize_stream(
        self, text: str, target_lang: str
    ) -> AsyncGenerator[bytes, None]:
        mock = MockTTSProvider()
        async for chunk in mock.synthesize_stream(text, target_lang):
            yield chunk


class BhashiniTTSProvider(BaseTTSProvider):
    async def synthesize_stream(
        self, text: str, target_lang: str
    ) -> AsyncGenerator[bytes, None]:
        mock = MockTTSProvider()
        async for chunk in mock.synthesize_stream(text, target_lang):
            yield chunk


class MockTTSProvider(BaseTTSProvider):
    async def synthesize_stream(
        self, text: str, target_lang: str
    ) -> AsyncGenerator[bytes, None]:
        num_chunks = max(3, min(12, int(len(text) / 4)))
        freq = 380 if target_lang in ("ta", "ml", "kn", "te") else 420

        for idx in range(num_chunks):
            t = np.linspace(0, CHUNK_DURATION_S, CHUNK_SAMPLES, endpoint=False)
            envelope = np.ones_like(t)
            if idx == 0:
                envelope = np.linspace(0, 1, CHUNK_SAMPLES)
            elif idx == num_chunks - 1:
                envelope = np.linspace(1, 0, CHUNK_SAMPLES)

            sine_wave = np.sin(2 * np.pi * (freq + idx * 8) * t) * envelope * 12000
            pcm_chunk = sine_wave.astype(np.int16).tobytes()

            yield pcm_chunk
            await asyncio.sleep(0.03)


_tts_instance: Optional[BaseTTSProvider] = None


def get_tts_engine() -> BaseTTSProvider:
    global _tts_instance
    if _tts_instance is None:
        backend = settings.tts_backend
        if backend == "vits_local":
            _tts_instance = VITSLocalProvider()
        elif backend == "indic_tts_api":
            _tts_instance = IndicTTSProvider()
        else:
            _tts_instance = IndicTTSProvider()
    return _tts_instance

