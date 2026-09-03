"""
TRANSLARA — Local Named Entity Recognition & Masking Service.
"""
from __future__ import annotations

from typing import Any, Dict, List
from backend.app.models.inference import infer_ner_local


class NERService:
    """
    Service layer for local NER extraction and token shielding.
    """

    @staticmethod
    def extract_entities(text: str) -> Dict[str, Any]:
        """Extract detected entities locally without external APIs."""
        return infer_ner_local(text)
