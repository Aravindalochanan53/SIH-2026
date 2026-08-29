"""
Central Translation Engine Orchestrator for TRANSLARA.
Manages provider priority chain (IndicTrans2 -> Bhashini -> Offline/Pivot),
Entity Locking, and Quality Validation.
"""
from __future__ import annotations

import time
from typing import Dict, List, Optional
from loguru import logger

from backend.ai.ner.entity_lock import get_entity_lock
from backend.ai.translation.base import BaseTranslationProvider, TranslationResult
from backend.ai.translation.bhashini_provider import BhashiniProvider
from backend.ai.translation.hybrid_pivot import PivotTranslationEngine
from backend.ai.translation.indictrans2_provider import IndicTrans2Provider
from backend.ai.translation.offline_provider import OfflineTranslationProvider
from backend.ai.translation.neural_grammar_engine import NeuralGrammarTranslationEngine
from backend.ai.validators.translation_validator import TranslationValidator
from backend.config import settings
from backend.ml_engine.languages import is_pair_supported


class TranslationEngine:
    """
    Modular Translation Orchestrator.
    Pipeline:
    1. Entity Recognition & Masking
    2. Model Provider Inference (IndicTrans2 / Bhashini / Neural Grammar AI / Offline / Pivot)
    3. Entity Restoration
    4. Translation & Script Validation
    """

    def __init__(self):
        self.entity_lock = get_entity_lock()
        self.indictrans2 = IndicTrans2Provider()
        self.bhashini = BhashiniProvider()
        self.offline = OfflineTranslationProvider()
        self.pivot = PivotTranslationEngine()
        self.neural_grammar = NeuralGrammarTranslationEngine()

    async def translate(
        self,
        text: str,
        source_lang: str = "ta",
        target_lang: str = "ml",
        preferred_engine: Optional[str] = None,
    ) -> TranslationResult:
        start_time = time.monotonic()
        src = source_lang.lower().strip()
        tgt = target_lang.lower().strip()

        if not text or not text.strip():
            return TranslationResult(
                text="",
                source_lang=src,
                target_lang=tgt,
                latency_ms=0.0,
                backend="none",
                confidence=0.0,
            )

        # 1. Detect & Mask Entities
        detected_entities = self.entity_lock.detect_entities(text)
        masked_text, token_map = self.entity_lock.mask(text, detected_entities)

        # 2. Select Provider
        selected_backend = preferred_engine or settings.nmt_backend
        provider: BaseTranslationProvider

        # Low-resource tribal routing (Santhali, Ho, Mundari)
        if tgt in ("sat", "hoc", "unr") or src in ("sat", "hoc", "unr"):
            provider = self.pivot
        elif selected_backend == "bhashini_ulca" and self.bhashini.is_pair_supported(src, tgt):
            provider = self.bhashini
        elif selected_backend in ("indictrans2", "indictrans2_local") and self.indictrans2.is_pair_supported(src, tgt) and self.indictrans2._ready:
            provider = self.indictrans2
        else:
            provider = self.neural_grammar

        # 3. Perform Inference
        raw_result = await provider.translate(masked_text, src, tgt)

        # 4. Unmask Entities
        restored_text = self.entity_lock.unmask(raw_result.text, token_map)

        # Fallback check: If raw output echoed source text, translate via neural grammar engine
        if restored_text.strip() == text.strip() and src != tgt:
            ng_result = await self.neural_grammar.translate(masked_text, src, tgt)
            restored_text = self.entity_lock.unmask(ng_result.text, token_map)
            raw_result = ng_result

        # 5. Validate Quality & Script Integrity
        expected_ents = [e.text for e in detected_entities]
        val = TranslationValidator.validate(
            source_text=text,
            translated_text=restored_text,
            source_lang=src,
            target_lang=tgt,
            expected_entities=expected_ents,
        )

        total_latency = (time.monotonic() - start_time) * 1000

        return TranslationResult(
            text=restored_text,
            source_lang=src,
            target_lang=tgt,
            latency_ms=total_latency,
            backend=raw_result.backend,
            confidence=val.confidence,
            pivot_used=raw_result.pivot_used,
            pivot_lang=raw_result.pivot_lang,
            warnings=list(set(raw_result.warnings + val.warnings)),
            script_purity=val.script_purity,
        )


# Singleton instance
_translation_engine_instance: Optional[TranslationEngine] = None


def get_translation_engine() -> TranslationEngine:
    global _translation_engine_instance
    if _translation_engine_instance is None:
        _translation_engine_instance = TranslationEngine()
    return _translation_engine_instance
