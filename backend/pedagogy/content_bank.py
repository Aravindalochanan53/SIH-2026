"""
Shared Multilingual Educational Content Bank for TRANSLARA.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass
class PhraseEntry:
    id: str
    category: str
    source_language: str
    target_language: str
    source_text: str
    target_text: str
    pronunciation: str = ""
    verified: bool = False
    status: str = "NEEDS_REVIEW"


# Multi-lingual educational vocabulary entries
SEED_ENTRIES = [
    PhraseEntry("vocab_01", "classroom", "ta", "ml", "புத்தகம்", "പുസ്തകം", "Puthagam -> Pusthakam", True, "VERIFIED"),
    PhraseEntry("vocab_02", "classroom", "ta", "ml", "எழுதுகோல்", "പേന", "Ezhuthukol -> Pena", True, "VERIFIED"),
    PhraseEntry("vocab_03", "classroom", "ta", "ml", "பள்ளி", "സ്കൂൾ", "Palli -> School", True, "VERIFIED"),
    PhraseEntry("vocab_04", "classroom", "ta", "ml", "ஆசிரியர்", "അധ്യാപകൻ", "Aasiriyar -> Adhyapakan", True, "VERIFIED"),
    PhraseEntry("vocab_05", "numbers", "ta", "ml", "ஒன்று (1)", "ഒന്ന് (1)", "Ondru -> Onnu", True, "VERIFIED"),
    PhraseEntry("vocab_06", "numbers", "ta", "ml", "இரண்டு (2)", "രണ്ട് (2)", "Irandu -> Randu", True, "VERIFIED"),
    PhraseEntry("vocab_07", "numbers", "ta", "ml", "மூன்று (3)", "മൂന്ന് (3)", "Moondru -> Moonnu", True, "VERIFIED"),
    PhraseEntry("vocab_08", "numbers", "ta", "ml", "நான்கு (4)", "നാല് (4)", "Naangu -> Naalu", True, "VERIFIED"),
    # English -> Tamil / Malayalam / Hindi
    PhraseEntry("vocab_en_ta_01", "classroom", "en", "ta", "Book", "புத்தகம்", "Book -> Puthagam", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_02", "classroom", "en", "ta", "Pen", "எழுதுகோல்", "Pen -> Ezhuthukol", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_03", "classroom", "en", "ta", "School", "பள்ளி", "School -> Palli", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_04", "classroom", "en", "ta", "Teacher", "ஆசிரியர்", "Teacher -> Aasiriyar", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_05", "numbers", "en", "ta", "One (1)", "ஒன்று (1)", "One -> Ondru", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_06", "numbers", "en", "ta", "Two (2)", "இரண்டு (2)", "Two -> Irandu", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_07", "numbers", "en", "ta", "Three (3)", "மூன்று (3)", "Three -> Moondru", True, "VERIFIED"),
    PhraseEntry("vocab_en_ta_08", "numbers", "en", "ta", "Four (4)", "நான்கு (4)", "Four -> Naangu", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_01", "classroom", "en", "ml", "Book", "പുസ്തകം", "Book -> Pusthakam", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_02", "classroom", "en", "ml", "Pen", "പേന", "Pen -> Pena", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_03", "classroom", "en", "ml", "School", "സ്കൂൾ", "School -> School", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_04", "classroom", "en", "ml", "Teacher", "അധ്യാപകൻ", "Teacher -> Adhyapakan", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_05", "numbers", "en", "ml", "One (1)", "ഒന്ന് (1)", "One -> Onnu", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_06", "numbers", "en", "ml", "Two (2)", "രണ്ട് (2)", "Two -> Randu", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_07", "numbers", "en", "ml", "Three (3)", "മൂന്ന് (3)", "Three -> Moonnu", True, "VERIFIED"),
    PhraseEntry("vocab_en_ml_08", "numbers", "en", "ml", "Four (4)", "നാല് (4)", "Four -> Naalu", True, "VERIFIED"),
    # Hindi -> Santhali / Tribal
    PhraseEntry("vocab_hi_sat_01", "classroom", "hi", "sat", "किताब", "ᱯᱩᱛᱷᱤ", "Kitaab -> Puthi", True, "VERIFIED"),
    PhraseEntry("vocab_hi_sat_02", "classroom", "hi", "sat", "कलम", "ᱠᱚᱞᱚᱢ", "Kalam -> Kolom", True, "VERIFIED"),
    PhraseEntry("vocab_hi_sat_03", "classroom", "hi", "sat", "स्कूल", "ᱤᱥᱠᱩᱞ", "School -> Iskul", True, "VERIFIED"),
    PhraseEntry("vocab_hi_sat_04", "classroom", "hi", "sat", "शिक्षक", "ᱢᱟᱪᱮᱛ", "Shikshak -> Machet", True, "VERIFIED"),
]


def get_entries_for_pair(source_lang: str, target_lang: str) -> list[PhraseEntry]:
    """Get content bank entries for a language pair, or return seed defaults."""
    matches = [
        e for e in SEED_ENTRIES
        if e.source_language == source_lang and e.target_language == target_lang
    ]
    if matches:
        return matches
    return SEED_ENTRIES
