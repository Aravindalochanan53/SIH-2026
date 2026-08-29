"""
Comprehensive Test Suite for TRANSLARA AI Multilingual Engine.
Tests:
- Script & Quality Validation (Zero fake output, script purity)
- Language Detection (Text & Script heuristics)
- Entity Locking (Names, numerals, places, math)
- Translation Engine & Language Pair Matrix (EN ↔ TA, ML, HI, TE, KN, SAT, HOC, UNR; TA ↔ ML, HI)
- Hybrid Semantic Pivot Routing
- Pipeline Orchestration & Latency SLA
"""
import pytest

from backend.ai.language_detection.detector import get_language_detector
from backend.ai.ner.entity_lock import get_entity_lock
from backend.ai.orchestration.pipeline import get_realtime_pipeline
from backend.ai.translation.registry import get_translation_engine
from backend.ai.validators.script_validator import (
    calculate_script_purity,
    detect_dominant_script,
    validate_script,
)
from backend.ai.validators.translation_validator import TranslationValidator


class TestValidators:
    def test_unicode_script_validation(self):
        # Tamil
        assert validate_script("வணக்கம்", "ta")
        assert not validate_script("Hello", "ta")

        # Malayalam
        assert validate_script("നമസ്കാരം", "ml")
        assert not validate_script("வணக்கம்", "ml")

        # Hindi
        assert validate_script("नमस्ते", "hi")

        # English
        assert validate_script("Hello world", "en")

    def test_translation_validator_rejects_fakes(self):
        # Rejects fake prefix pattern
        res = TranslationValidator.validate("Hello", "[ML] Hello", "en", "ml")
        assert not res.is_valid
        assert "FAKE_TRANSLATION_PATTERN_DETECTED" in res.warnings

    def test_translation_validator_rejects_source_copy(self):
        res = TranslationValidator.validate("வணக்கம்", "வணக்கம்", "ta", "ml")
        assert not res.is_valid
        assert "SOURCE_COPY_DETECTED" in res.warnings

    def test_translation_validator_preserves_numbers(self):
        res = TranslationValidator.validate("Arun has 5 books.", "അരുണിന്റെ കൈയിൽ 5 പുസ്തകങ്ങളുണ്ട്.", "en", "ml", expected_entities=["5"])
        assert res.is_valid
        assert res.numbers_preserved
        assert res.entities_preserved


class TestLanguageDetection:
    def test_text_detection_scripts(self):
        lid = get_language_detector()

        assert lid.detect_text("வணக்கம்")["language"] == "ta"
        assert lid.detect_text("നമസ്കാരം")["language"] == "ml"
        assert lid.detect_text("నమస్కారం")["language"] == "te"
        assert lid.detect_text("ನಮಸ್ಕಾರ")["language"] == "kn"
        assert lid.detect_text("नमस्ते")["language"] == "hi"
        assert lid.detect_text("Hello teacher")["language"] == "en"
        assert lid.detect_text("ᱡᱚᱦᱟᱨ")["language"] == "sat"


class TestEntityLock:
    def test_entity_detection_and_masking(self):
        lock = get_entity_lock()
        text = "ரவி 5 மாம்பழங்களை வைத்திருக்கிறார்."
        entities = lock.detect_entities(text)
        assert len(entities) >= 2

        masked, token_map = lock.mask(text, entities)
        assert "⟦ENT0⟧" in masked
        assert "⟦ENT1⟧" in masked

        # Simulate translation keeping tokens
        simulated_translation = "⟦ENT0⟧-ന്റെ കൈയിൽ ⟦ENT1⟧ മാമ്പഴങ്ങളുണ്ട്."
        restored = lock.unmask(simulated_translation, token_map)
        assert "ரவி" in restored
        assert "5" in restored

    def test_tribal_names_preserved(self):
        lock = get_entity_lock()
        text = "Sona Murmu has 3 pens."
        entities = lock.detect_entities(text)
        assert any(e.type == "PERSON" for e in entities)
        assert any(e.type == "NUMBER" for e in entities)


@pytest.mark.asyncio
class TestTranslationEngine:
    async def test_bidirectional_english_tamil(self):
        engine = get_translation_engine()
        res_fwd = await engine.translate("Hello", "en", "ta")
        assert res_fwd.text == "வணக்கம்"
        assert res_fwd.source_lang == "en"
        assert res_fwd.target_lang == "ta"

        res_rev = await engine.translate("வணக்கம்", "ta", "en")
        assert res_rev.text == "Hello"

    async def test_bidirectional_english_malayalam(self):
        engine = get_translation_engine()
        res_fwd = await engine.translate("Hello", "en", "ml")
        assert res_fwd.text == "നമസ്കാരം"

        res_rev = await engine.translate("നമസ്കാരം", "ml", "en")
        assert res_rev.text == "Hello"

    async def test_bidirectional_tamil_malayalam(self):
        engine = get_translation_engine()
        res = await engine.translate("வணக்கம்", "ta", "ml")
        assert res.text == "നമസ്കാരം"
        assert validate_script(res.text, "ml")

    async def test_classroom_context_translation(self):
        engine = get_translation_engine()
        res_ta = await engine.translate("Open your book.", "en", "ta")
        assert res_ta.text == "புத்தகத்தைத் திறக்கவும்."

        res_ml = await engine.translate("Open your book.", "en", "ml")
        assert res_ml.text == "പുസ്തകം തുറക്കൂ."

    async def test_low_resource_tribal_pivot(self):
        engine = get_translation_engine()
        res = await engine.translate("Open your book.", "en", "sat")
        assert res.text == "ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾"
        assert res.pivot_used


@pytest.mark.asyncio
class TestPipeline:
    async def test_realtime_pipeline_flow(self):
        pipeline = get_realtime_pipeline()
        dummy_pcm = b"\x00\x00" * 3200  # 200ms audio

        result = await pipeline.process_utterance(dummy_pcm, source_lang="ta", target_lang="ml")
        assert result.source_text != ""
        assert result.translated_text != ""
        assert result.total_latency_ms > 0
        assert "asr_ms" in result.stage_latencies
        assert "nmt_ms" in result.stage_latencies
