"""
Unit tests for TRANSLARA Multilingual Pedagogy & PDF Generation.
"""
from pathlib import Path
from backend.pedagogy.content_bank import SEED_ENTRIES
from backend.pedagogy.flashcard_generator import generate_flashcard_pdf
from backend.pedagogy.fonts import get_font_for_language, register_all_fonts
from backend.pedagogy.worksheet_generator import (
    generate_matching_worksheet_pdf,
    generate_numeracy_worksheet_pdf,
)


def test_font_registry_and_resolution():
    register_all_fonts()
    for lang in ("ta", "te", "kn", "ml", "hi", "sat"):
        font = get_font_for_language(lang)
        assert font is not None


def test_pdf_renders_tamil(tmp_path):
    """TEST 13: PDF renders Tamil."""
    out = tmp_path / "flashcards_ta_ml.pdf"
    res = generate_flashcard_pdf(SEED_ENTRIES[:4], source_lang="ta", target_lang="ml", output_path=out)
    assert res.exists()
    assert res.stat().st_size > 1000


def test_pdf_renders_telugu(tmp_path):
    """TEST 14: PDF renders Telugu."""
    out = tmp_path / "numeracy_te_ta.pdf"
    res = generate_numeracy_worksheet_pdf(output_path=out, source_lang="te", target_lang="ta", grade=1)
    assert res.exists()
    assert res.stat().st_size > 1000


def test_pdf_renders_kannada(tmp_path):
    """TEST 15: PDF renders Kannada."""
    out = tmp_path / "numeracy_kn_ml.pdf"
    res = generate_numeracy_worksheet_pdf(output_path=out, source_lang="kn", target_lang="ml", grade=2)
    assert res.exists()
    assert res.stat().st_size > 1000


def test_pdf_renders_malayalam(tmp_path):
    """TEST 16: PDF renders Malayalam."""
    out = tmp_path / "matching_ml_ta.pdf"
    res = generate_matching_worksheet_pdf(output_path=out, source_lang="ml", target_lang="ta", grade=1)
    assert res.exists()
    assert res.stat().st_size > 1000
