"""
Multilingual Language Detector for TRANSLARA.
Supports text and audio language identification across Indian languages and English:
en, ta, te, kn, ml, hi, sat, hoc, unr.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Optional
from loguru import logger

from backend.ai.validators.script_validator import SCRIPT_UNICODE_RANGES, detect_dominant_script


class LanguageDetector:
    """
    High-precision Language Detector using Unicode Script Heuristics and optional ML models.
    """

    def __init__(self):
        self._has_langdetect = False
        try:
            import langdetect
            self._has_langdetect = True
        except ImportError:
            self._has_langdetect = False

    def detect_text(self, text: str) -> Dict[str, Any]:
        """
        Detect the language of text input.
        Returns:
            {"language": str, "confidence": float, "method": str}
        """
        clean_text = text.strip()
        if not clean_text:
            return {"language": "en", "confidence": 0.0, "method": "fallback"}

        # 1. Check Unicode script heuristic (very fast & 100% deterministic for Indian scripts)
        script_lang = detect_dominant_script(clean_text)
        if script_lang:
            # Special check for English (ASCII alphabetic)
            if script_lang == "en":
                return {
                    "language": "en",
                    "confidence": 0.99,
                    "method": "unicode_script_heuristic",
                }

            return {
                "language": script_lang,
                "confidence": 0.98,
                "method": "unicode_script_heuristic",
            }

        # 2. Fallback to langdetect if available
        if self._has_langdetect:
            try:
                import langdetect
                detected = langdetect.detect(clean_text)
                return {
                    "language": detected,
                    "confidence": 0.90,
                    "method": "langdetect_model",
                }
            except Exception:
                pass

        # 3. Default fallback
        return {
            "language": "en",
            "confidence": 0.50,
            "method": "default_fallback",
        }

    async def detect_audio(self, pcm16_bytes: bytes, asr_provider: Optional[Any] = None) -> Dict[str, Any]:
        """
        Detect language of spoken audio via ASR or acoustic feature classification.
        """
        if asr_provider is not None:
            try:
                lang = await asr_provider.detect_language(pcm16_bytes)
                return {
                    "language": lang,
                    "confidence": 0.94,
                    "method": "asr_acoustic_lid",
                }
            except Exception as e:
                logger.warning(f"Audio language detection via ASR failed: {e}")

        return {
            "language": "ta",
            "confidence": 0.70,
            "method": "audio_default",
        }


# Singleton instance
_detector_instance: Optional[LanguageDetector] = None


def get_language_detector() -> LanguageDetector:
    global _detector_instance
    if _detector_instance is None:
        _detector_instance = LanguageDetector()
    return _detector_instance
