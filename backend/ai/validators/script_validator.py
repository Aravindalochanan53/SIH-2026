"""
Unicode script validation for Indian languages and English.
"""
from __future__ import annotations

import unicodedata
from typing import Optional

SCRIPT_UNICODE_RANGES = {
    "ta": [(0x0B80, 0x0BFF)],          # Tamil
    "te": [(0x0C00, 0x0C7F)],          # Telugu
    "kn": [(0x0C80, 0x0CFF)],          # Kannada
    "ml": [(0x0D00, 0x0D7F)],          # Malayalam
    "hi": [(0x0900, 0x097F)],          # Devanagari (Hindi)
    "sat": [(0x1C50, 0x1C7F)],         # Ol Chiki (Santhali)
    "hoc": [(0x0900, 0x097F)],         # Devanagari / Ho
    "unr": [(0x0900, 0x097F)],         # Devanagari / Mundari
    "en": [(0x0041, 0x005A), (0x0061, 0x007A)], # Latin (English)
}


def is_char_in_script(char: str, lang_code: str) -> bool:
    """Check if a single character belongs to the script of the given language code."""
    code_point = ord(char)
    ranges = SCRIPT_UNICODE_RANGES.get(lang_code.lower())
    if not ranges:
        return True
    return any(start <= code_point <= end for start, end in ranges)


def calculate_script_purity(text: str, lang_code: str) -> float:
    """
    Calculate the ratio of alphabetic characters in `text` matching `lang_code`'s script.
    Ignores whitespace, ASCII digits, punctuation, and entity tokens (⟦ENT...⟧ / <ENT...>).
    """
    cleaned = text
    # Remove entity tags
    import re
    cleaned = re.sub(r"⟦ENT\d+⟧|<[A-Z_]+_\d+>|\[ENT\d+\]", "", cleaned)

    alpha_chars = [c for c in cleaned if c.isalpha()]
    if not alpha_chars:
        return 1.0

    matching_chars = [c for c in alpha_chars if is_char_in_script(c, lang_code)]
    return len(matching_chars) / len(alpha_chars)


def validate_script(text: str, expected_lang: str, min_purity: float = 0.50) -> bool:
    """
    Validate that the translated text is primarily written in the expected script.
    """
    purity = calculate_script_purity(text, expected_lang)
    return purity >= min_purity


def detect_dominant_script(text: str) -> Optional[str]:
    """Detect the dominant script of a given text."""
    import re
    cleaned = re.sub(r"⟦ENT\d+⟧|<[A-Z_]+_\d+>|\[ENT\d+\]", "", text)
    alpha_chars = [c for c in cleaned if c.isalpha()]
    if not alpha_chars:
        return None

    scores = {}
    for lang_code in SCRIPT_UNICODE_RANGES:
        scores[lang_code] = calculate_script_purity(cleaned, lang_code)

    best_lang, best_score = max(scores.items(), key=lambda x: x[1])
    return best_lang if best_score >= 0.40 else None
