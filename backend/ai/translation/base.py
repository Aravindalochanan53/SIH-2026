"""
Base Translation Provider Interface for TRANSLARA.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class TranslationResult:
    text: str
    source_lang: str
    target_lang: str
    latency_ms: float
    backend: str
    confidence: float = 1.0
    detected_lang: Optional[str] = None
    pivot_used: bool = False
    pivot_lang: Optional[str] = None
    warnings: List[str] = field(default_factory=list)
    script_purity: float = 1.0


class BaseTranslationProvider:
    """Abstract Base Class for modular NMT Translation backends."""

    async def translate(
        self, text: str, source_lang: str, target_lang: str
    ) -> TranslationResult:
        raise NotImplementedError

    def is_pair_supported(self, source_lang: str, target_lang: str) -> bool:
        """Check if this provider natively supports the language pair."""
        return True
