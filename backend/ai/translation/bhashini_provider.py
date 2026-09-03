"""
Local Translation Engine (Deprecated BhashiniProvider replacement).
Directs all requests exclusively to local translation models.
"""
from __future__ import annotations

from backend.ai.translation.base import BaseTranslationProvider, TranslationResult
from backend.ai.translation.neural_grammar_engine import NeuralGrammarTranslationEngine


class BhashiniProvider(BaseTranslationProvider):
    """
    Local fallback provider replacing external Bhashini cloud APIs.
    Runs 100% offline via local Neural Grammar engine.
    """

    def __init__(self):
        self._local_engine = NeuralGrammarTranslationEngine()

    def is_pair_supported(self, source_lang: str, target_lang: str) -> bool:
        return True

    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        res = await self._local_engine.translate(text, source_lang, target_lang)
        return TranslationResult(
            text=res.text,
            source_lang=source_lang,
            target_lang=target_lang,
            latency_ms=res.latency_ms,
            backend="local_nmt",
            confidence=0.95,
        )
