"""
A4 Printable Bilingual Flashcard PDF Generator for TRANSLARA.

Renders 8 flashcards (2 columns x 4 rows) per A4 page.
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence
from loguru import logger
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from backend.ml_engine.languages import get_language
from backend.pedagogy.content_bank import PhraseEntry
from backend.pedagogy.fonts import get_font_for_language
from backend.pedagogy.templates import (
    COLOR_BORDER,
    COLOR_DARK,
    COLOR_MUTED,
    COLOR_TEAL,
    MARGIN,
    PAGE_H,
    PAGE_W,
    PRINTABLE_H,
    PRINTABLE_W,
    draw_pedagogy_footer,
    draw_pedagogy_header,
)

CATEGORY_COLORS: dict[str, HexColor] = {
    "classroom": HexColor("#0f766e"),
    "numbers": HexColor("#ea580c"),
    "greetings": HexColor("#2563eb"),
    "courtesy": HexColor("#7c3aed"),
    "general": HexColor("#475569"),
}


def generate_flashcard_pdf(
    entries: Sequence[PhraseEntry],
    source_lang: str = "ta",
    target_lang: str = "ml",
    output_path: Path = Path("flashcards.pdf"),
    title: str = "Bilingual Vocabulary Flashcards",
) -> Path:
    """Generate printable 2x4 A4 bilingual flashcards."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)

    src_cfg = get_language(source_lang)
    tgt_cfg = get_language(target_lang)
    src_name = src_cfg.name if src_cfg else source_lang.upper()
    tgt_name = tgt_cfg.name if tgt_cfg else target_lang.upper()

    src_font = get_font_for_language(source_lang)
    tgt_font = get_font_for_language(target_lang)

    cards_per_page = 8
    chunks = [entries[i : i + cards_per_page] for i in range(0, len(entries), cards_per_page)] or [[]]

    for page_idx, page_entries in enumerate(chunks, start=1):
        content_top_y = draw_pedagogy_header(
            c,
            title=title,
            source_lang=source_lang,
            target_lang=target_lang,
            subtitle=f"Classroom vocabulary matching {src_name} and {tgt_name}",
        )

        grid_top = content_top_y - 2 * mm
        grid_bottom = MARGIN + 12 * mm
        grid_height = grid_top - grid_bottom
        grid_width = PRINTABLE_W

        cols = 2
        rows = 4
        gutter = 4 * mm
        card_w = (grid_width - (cols - 1) * gutter) / cols
        card_h = (grid_height - (rows - 1) * gutter) / rows

        for idx, entry in enumerate(page_entries):
            col_idx = idx % cols
            row_idx = idx // cols

            card_x = MARGIN + col_idx * (card_w + gutter)
            card_y = grid_top - (row_idx + 1) * card_h - row_idx * gutter

            cat_color = CATEGORY_COLORS.get(entry.category, CATEGORY_COLORS["general"])

            # Card background & border
            c.setFillColor(white)
            c.setStrokeColor(COLOR_BORDER)
            c.setLineWidth(1)
            c.roundRect(card_x, card_y, card_w, card_h, 3 * mm, fill=1, stroke=1)

            # Category top stripe
            c.setFillColor(cat_color)
            c.rect(card_x, card_y + card_h - 4 * mm, card_w, 4 * mm, fill=1, stroke=0)

            # Category text
            c.setFont("Helvetica-Bold", 6.5)
            c.setFillColor(white)
            c.drawString(card_x + 3 * mm, card_y + card_h - 3 * mm, entry.category.upper())

            # Source Language Text
            c.setFont(src_font, 13)
            c.setFillColor(COLOR_DARK)
            c.drawCentredString(card_x + card_w / 2, card_y + card_h - 13 * mm, entry.source_text)

            # Target Language Text
            c.setFont(tgt_font, 14)
            c.setFillColor(cat_color)
            c.drawCentredString(card_x + card_w / 2, card_y + card_h - 22 * mm, entry.target_text)

            # Pronunciation hint
            if entry.pronunciation:
                c.setFont("Helvetica-Oblique", 7)
                c.setFillColor(COLOR_MUTED)
                c.drawCentredString(card_x + card_w / 2, card_y + 4 * mm, entry.pronunciation[:40])

        draw_pedagogy_footer(c, page_num=page_idx, total_pages=len(chunks))
        c.showPage()

    c.save()
    logger.info(f"Flashcard PDF generated: {output_path} ({len(entries)} items)")
    return output_path
