"""
Base interface for Automatic Speech Recognition (ASR) providers in TRANSLARA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class ASRResult:
    text: str
    language: str
    confidence: float
    latency_ms: float
    backend: str


class BaseASRProvider:
    """Abstract Base Class for modular ASR backends."""

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> ASRResult:
        """Transcribe raw PCM16 16kHz audio bytes to text."""
        raise NotImplementedError

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        """Detect language code of the spoken audio."""
        raise NotImplementedError
