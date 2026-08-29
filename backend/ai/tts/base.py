"""
Base TTS Provider Interface for TRANSLARA.
"""
from __future__ import annotations

from typing import AsyncGenerator


class BaseTTSProvider:
    """Abstract Base Class for Text-to-Speech synthesis."""

    async def synthesize_stream(
        self, text: str, target_lang: str
    ) -> AsyncGenerator[bytes, None]:
        raise NotImplementedError
        yield b""
