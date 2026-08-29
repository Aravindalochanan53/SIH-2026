"""
TRANSLARA — Centralized Language Registry and Capability Matrix.

Single source of truth for all supported Indian languages, regional grouping,
scripts, FLORES-200 / Bhashini language tags, and model capability detection.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class LanguageConfig:
    code: str                  # ISO 639-1 / 639-3 code (e.g. "ta", "te", "kn", "ml", "hi", "sat")
    name: str                  # English name (e.g. "Tamil", "Telugu")
    native_name: str           # Native script name (e.g. "தமிழ்", "తెలుగు")
    region: str                # Regional grouping: "South India" | "North / Other India" | "Eastern India"
    script: str                # Script family: "Tamil", "Telugu", "Kannada", "Malayalam", "Devanagari", "Ol Chiki", "Warang Citi"
    indictrans2_tag: str       # FLORES-200 tag for IndicTrans2 (e.g. "tam_Taml", "tel_Telu")
    bhashini_code: str         # Bhashini ULCA language code (e.g. "ta", "te")
    asr_supported: bool = True
    translation_supported: bool = True
    tts_supported: bool = True
    offline_supported: bool = True
    font_name: str = "Helvetica"
    font_file: str = "NotoSans-Regular.ttf"


# ====================================================================== #
# Central Language Registry
# ====================================================================== #

LANGUAGES: dict[str, LanguageConfig] = {
    # --- English ---
    "en": LanguageConfig(
        code="en",
        name="English",
        native_name="English",
        region="English",
        script="Latin",
        indictrans2_tag="eng_Latn",
        bhashini_code="en",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="Helvetica",
        font_file="NotoSans-Regular.ttf",
    ),

    # --- South Indian Languages (First-Class Citizens) ---
    "ta": LanguageConfig(
        code="ta",
        name="Tamil",
        native_name="தமிழ்",
        region="South India",
        script="Tamil",
        indictrans2_tag="tam_Taml",
        bhashini_code="ta",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansTamil",
        font_file="NotoSansTamil-Regular.ttf",
    ),
    "te": LanguageConfig(
        code="te",
        name="Telugu",
        native_name="తెలుగు",
        region="South India",
        script="Telugu",
        indictrans2_tag="tel_Telu",
        bhashini_code="te",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansTelugu",
        font_file="NotoSansTelugu-Regular.ttf",
    ),
    "kn": LanguageConfig(
        code="kn",
        name="Kannada",
        native_name="ಕನ್ನಡ",
        region="South India",
        script="Kannada",
        indictrans2_tag="kan_Knda",
        bhashini_code="kn",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansKannada",
        font_file="NotoSansKannada-Regular.ttf",
    ),
    "ml": LanguageConfig(
        code="ml",
        name="Malayalam",
        native_name="മലയാളം",
        region="South India",
        script="Malayalam",
        indictrans2_tag="mal_Mlym",
        bhashini_code="ml",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansMalayalam",
        font_file="NotoSansMalayalam-Regular.ttf",
    ),

    # --- North & Other Indian Languages ---
    "hi": LanguageConfig(
        code="hi",
        name="Hindi",
        native_name="हिन्दी",
        region="North / Other India",
        script="Devanagari",
        indictrans2_tag="hin_Deva",
        bhashini_code="hi",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansDevanagari",
        font_file="NotoSansDevanagari-Regular.ttf",
    ),
    "sat": LanguageConfig(
        code="sat",
        name="Santhali",
        native_name="ᱥᱟᱱᱛᱟᱲᱤ",
        region="North / Other India",
        script="Ol Chiki",
        indictrans2_tag="sat_Olck",
        bhashini_code="sat",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=True,
        font_name="NotoSansOlChiki",
        font_file="NotoSansOlChiki-Regular.ttf",
    ),
    "hoc": LanguageConfig(
        code="hoc",
        name="Ho",
        native_name="Ho (हो)",
        region="North / Other India",
        script="Devanagari",
        indictrans2_tag="hoc_Deva",
        bhashini_code="hoc",
        asr_supported=True,
        translation_supported=True,
        tts_supported=False,
        offline_supported=True,
        font_name="NotoSansDevanagari",
        font_file="NotoSansDevanagari-Regular.ttf",
    ),
    "unr": LanguageConfig(
        code="unr",
        name="Mundari",
        native_name="Mundari (मुंडारी)",
        region="North / Other India",
        script="Devanagari",
        indictrans2_tag="unr_Deva",
        bhashini_code="unr",
        asr_supported=True,
        translation_supported=True,
        tts_supported=False,
        offline_supported=True,
        font_name="NotoSansDevanagari",
        font_file="NotoSansDevanagari-Regular.ttf",
    ),

    # --- Extensible Indian Languages (Ready for registry activation) ---
    "bn": LanguageConfig(
        code="bn",
        name="Bengali",
        native_name="বাংলা",
        region="Eastern India",
        script="Bengali",
        indictrans2_tag="ben_Beng",
        bhashini_code="bn",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=False,
        font_name="NotoSansBengali",
        font_file="NotoSansBengali-Regular.ttf",
    ),
    "mr": LanguageConfig(
        code="mr",
        name="Marathi",
        native_name="मराठी",
        region="Western India",
        script="Devanagari",
        indictrans2_tag="mar_Deva",
        bhashini_code="mr",
        asr_supported=True,
        translation_supported=True,
        tts_supported=True,
        offline_supported=False,
        font_name="NotoSansDevanagari",
        font_file="NotoSansDevanagari-Regular.ttf",
    ),
}


def get_language(code: str) -> Optional[LanguageConfig]:
    """Look up language configuration by code."""
    return LANGUAGES.get(code.lower().strip())


def get_all_languages() -> list[LanguageConfig]:
    """Return list of all registered languages."""
    return list(LANGUAGES.values())


def get_grouped_languages() -> dict[str, list[dict]]:
    """Return languages grouped for UI dropdowns."""
    grouped: dict[str, list[dict]] = {
        "English": [],
        "South India": [],
        "North / Other India": [],
        "Other Languages": [],
    }

    for lang in LANGUAGES.values():
        item = {
            "code": lang.code,
            "name": lang.name,
            "native_name": lang.native_name,
            "region": lang.region,
            "script": lang.script,
            "asr_supported": lang.asr_supported,
            "translation_supported": lang.translation_supported,
            "tts_supported": lang.tts_supported,
            "offline_supported": lang.offline_supported,
        }
        if lang.code == "en":
            grouped["English"].append(item)
        elif lang.region in grouped:
            grouped[lang.region].append(item)
        else:
            grouped["Other Languages"].append(item)

    return grouped


def get_capabilities_matrix(active_nmt_backend: str = "indictrans2") -> dict[str, dict]:
    """
    Return dynamic capability matrix indicating whether ASR, NMT, and TTS
    are available for each language and language pair.
    """
    matrix: dict[str, dict] = {}
    for code, lang in LANGUAGES.items():
        matrix[code] = {
            "name": lang.name,
            "native_name": lang.native_name,
            "region": lang.region,
            "asr": lang.asr_supported,
            "translation": lang.translation_supported,
            "tts": lang.tts_supported,
            "offline": lang.offline_supported,
        }
    return matrix


def is_pair_supported(src_lang: str, tgt_lang: str) -> bool:
    """Validate whether translation between src and tgt is supported."""
    src = get_language(src_lang)
    tgt = get_language(tgt_lang)
    if not src or not tgt:
        return False
    if src.code == tgt.code:
        return False
    return src.translation_supported and tgt.translation_supported
