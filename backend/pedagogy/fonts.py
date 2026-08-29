"""
Font Registry and Unicode Renderer for TRANSLARA PDF Generation.

Registers TrueType fonts for:
- Tamil (NotoSansTamil)
- Telugu (NotoSansTelugu)
- Kannada (NotoSansKannada)
- Malayalam (NotoSansMalayalam)
- Devanagari (NotoSansDevanagari - Hindi, Ho, Mundari)
- Ol Chiki (NotoSansOlChiki - Santhali)

Falls back safely to Helvetica when physical font files are missing.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional
from loguru import logger
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from backend.config import settings

# Mapping of script / language code to font metadata
FONT_DEFINITIONS = {
    "ta": {
        "name": "NotoSansTamil",
        "file": "NotoSansTamil-Regular.ttf",
        "env_override": "tamil_font_path",
    },
    "te": {
        "name": "NotoSansTelugu",
        "file": "NotoSansTelugu-Regular.ttf",
        "env_override": "telugu_font_path",
    },
    "kn": {
        "name": "NotoSansKannada",
        "file": "NotoSansKannada-Regular.ttf",
        "env_override": "kannada_font_path",
    },
    "ml": {
        "name": "NotoSansMalayalam",
        "file": "NotoSansMalayalam-Regular.ttf",
        "env_override": "malayalam_font_path",
    },
    "hi": {
        "name": "NotoSansDevanagari",
        "file": "NotoSansDevanagari-Regular.ttf",
        "env_override": "hindi_font_path",
    },
    "sat": {
        "name": "NotoSansOlChiki",
        "file": "NotoSansOlChiki-Regular.ttf",
        "env_override": "santhali_font_path",
    },
    "hoc": {
        "name": "NotoSansDevanagari",
        "file": "NotoSansDevanagari-Regular.ttf",
        "env_override": "ho_font_path",
    },
    "unr": {
        "name": "NotoSansDevanagari",
        "file": "NotoSansDevanagari-Regular.ttf",
        "env_override": "mundari_font_path",
    },
}

_REGISTERED_FONTS: dict[str, str] = {}


def register_all_fonts() -> None:
    """Register Indian language TrueType fonts with ReportLab."""
    fonts_dir = Path(settings.fonts_dir)

    for code, info in FONT_DEFINITIONS.items():
        font_name = info["name"]
        font_file = info["file"]
        env_attr = info["env_override"]
        custom_path = getattr(settings, env_attr, "")

        # Candidate paths
        candidates = [
            Path(custom_path) if custom_path else None,
            fonts_dir / font_file,
            Path("C:/Windows/Fonts") / font_file,
        ]

        resolved_path: Optional[Path] = None
        for cand in candidates:
            if cand and cand.exists() and cand.is_file():
                resolved_path = cand
                break

        if resolved_path:
            try:
                pdfmetrics.registerFont(TTFont(font_name, str(resolved_path)))
                _REGISTERED_FONTS[code] = font_name
                logger.info(f"Registered font '{font_name}' from {resolved_path}")
            except Exception as e:
                logger.warning(f"Failed to register font '{font_name}': {e}; falling back to Helvetica")
                _REGISTERED_FONTS[code] = "Helvetica"
        else:
            _REGISTERED_FONTS[code] = "Helvetica"


def get_font_for_language(lang_code: str) -> str:
    """Return the registered ReportLab font name for a language."""
    if not _REGISTERED_FONTS:
        register_all_fonts()
    return _REGISTERED_FONTS.get(lang_code.lower().strip(), "Helvetica")


def get_font_status() -> dict[str, str]:
    """Return map of language codes to active font names."""
    if not _REGISTERED_FONTS:
        register_all_fonts()
    return dict(_REGISTERED_FONTS)
