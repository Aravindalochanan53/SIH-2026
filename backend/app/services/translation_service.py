"""
TRANSLARA — Local Translation Service.

Executes translation exclusively through locally hosted and loaded models.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional
from backend.app.models.inference import infer_translation_local
from backend.ai.validators.script_validator import ScriptValidator


class TranslationService:
    """
    Service layer for local translation processing.
    """

    @staticmethod
    async def translate_text(
        text: str,
        source_lang: str = "ta",
        target_lang: str = "ml",
    ) -> Dict[str, Any]:
        """Translate a single text string locally."""
        result = await infer_translation_local(text, source_lang, target_lang)

        # Validate target script purity
        target_code = result.get("target_lang", target_lang)
        translated_text = result.get("translation", "")
        script_val = ScriptValidator.validate(translated_text, target_code)

        result["script_valid"] = script_val.is_valid
        result["script_purity"] = script_val.purity_ratio
        return result

    @staticmethod
    async def translate_batch(
        texts: List[str],
        source_lang: str = "ta",
        target_lang: str = "ml",
    ) -> List[Dict[str, Any]]:
        """Translate a list of texts in batch locally."""
        results = []
        for text in texts:
            res = await TranslationService.translate_text(text, source_lang, target_lang)
            results.append(res)
        return results
