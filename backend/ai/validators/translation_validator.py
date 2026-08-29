"""
Translation Quality and Correctness Validator for TRANSLARA.
Ensures zero fake translations, script integrity, and strict entity preservation.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Optional

from backend.ai.validators.script_validator import calculate_script_purity, validate_script


@dataclass
class ValidationResult:
    is_valid: bool
    confidence: float
    warnings: List[str]
    detected_script: Optional[str] = None
    script_purity: float = 1.0
    numbers_preserved: bool = True
    entities_preserved: bool = True


class TranslationValidator:
    """
    Validates machine translation outputs against source text.
    Enforces that:
    1. Output is non-empty.
    2. Output is not a verbatim copy of the source (unless source and target scripts share digits/punctuation).
    3. Output does not contain fake prefix patterns like '[ML]', '[TAMIL]', etc.
    4. Target script is correct.
    5. Numbers and locked entities are preserved.
    """

    # Fake prefix detector
    _FAKE_PREFIX_PATTERN = re.compile(r"^\[([a-zA-Z]{2,10}|[a-zA-Z_]+)\s*:\s*.*\]$|^\[[A-Z]{2,4}\]\s*", re.IGNORECASE)

    @classmethod
    def extract_numbers(cls, text: str) -> List[str]:
        """Extract all integer and floating point numbers from text."""
        return re.findall(r"\b\d+(?:\.\d+)?\b", text)

    @classmethod
    def validate(
        cls,
        source_text: str,
        translated_text: str,
        source_lang: str,
        target_lang: str,
        expected_entities: Optional[List[str]] = None,
    ) -> ValidationResult:
        warnings: List[str] = []
        is_valid = True
        confidence = 1.0

        # 1. Non-empty check
        src_clean = source_text.strip()
        tgt_clean = translated_text.strip()

        if not tgt_clean:
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                warnings=["EMPTY_TRANSLATION_OUTPUT"],
                script_purity=0.0,
                numbers_preserved=False,
                entities_preserved=False,
            )

        # 2. Fake pattern check (e.g. "[ML] hello")
        if cls._FAKE_PREFIX_PATTERN.match(tgt_clean):
            return ValidationResult(
                is_valid=False,
                confidence=0.0,
                warnings=["FAKE_TRANSLATION_PATTERN_DETECTED"],
                script_purity=0.0,
            )

        # 3. Source-copy detection (if source_lang != target_lang and text contains alphabetic characters)
        has_alpha = any(c.isalpha() for c in src_clean)
        if source_lang != target_lang and has_alpha and src_clean == tgt_clean:
            is_valid = False
            warnings.append("SOURCE_COPY_DETECTED")
            confidence = 0.20

        # 4. Target script validation
        purity = calculate_script_purity(tgt_clean, target_lang)
        if purity < 0.35 and has_alpha:
            is_valid = False
            warnings.append(f"SCRIPT_MISMATCH_EXPECTED_{target_lang.upper()}")
            confidence = min(confidence, 0.40)
        elif purity < 0.60 and has_alpha:
            warnings.append(f"LOW_SCRIPT_PURITY_{target_lang.upper()}")
            confidence = min(confidence, 0.75)

        # 5. Number preservation check
        src_numbers = set(cls.extract_numbers(src_clean))
        tgt_numbers = set(cls.extract_numbers(tgt_clean))
        numbers_preserved = True
        missing_numbers = src_numbers - tgt_numbers
        if missing_numbers:
            numbers_preserved = False
            warnings.append(f"NUMBERS_MUTATED_OR_DROPPED: {list(missing_numbers)}")
            confidence = min(confidence, 0.80)

        # 6. Entity preservation check
        entities_preserved = True
        if expected_entities:
            for ent in expected_entities:
                if ent and ent not in tgt_clean:
                    entities_preserved = False
                    warnings.append(f"MISSING_PROTECTED_ENTITY: {ent}")
                    confidence = min(confidence, 0.85)

        return ValidationResult(
            is_valid=is_valid,
            confidence=round(confidence, 2),
            warnings=warnings,
            script_purity=round(purity, 2),
            numbers_preserved=numbers_preserved,
            entities_preserved=entities_preserved,
        )
