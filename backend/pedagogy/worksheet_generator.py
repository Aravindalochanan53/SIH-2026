"""
FLN Numeracy and Literacy Worksheet Engine for TRANSLARA.

Supports bilingual counting, dot counters, handwriting trace lines, and word-matching worksheets
for Tamil, Telugu, Kannada, Malayalam, Hindi, Santhali, etc.
"""
from __future__ import annotations

import random
from pathlib import Path
from loguru import logger
from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from backend.ml_engine.languages import get_language
from backend.pedagogy.content_bank import SEED_ENTRIES
from backend.pedagogy.fonts import get_font_for_language
from backend.pedagogy.templates import (
    COLOR_BORDER,
    COLOR_DARK,
    COLOR_MUTED,
    COLOR_ORANGE,
    COLOR_TEAL,
    MARGIN,
    PAGE_W,
    PRINTABLE_W,
    draw_pedagogy_footer,
    draw_pedagogy_header,
)

NUMERAL_DATA = [
    {"val": 1, "ta": "ஒன்று", "ml": "ഒന്ന്", "te": "ఒకటి", "kn": "ಒಂದು", "hi": "एक", "sat": "ᱢᱤᱫ"},
    {"val": 2, "ta": "இரண்டு", "ml": "രണ്ട്", "te": "రెండు", "kn": "ಎರಡು", "hi": "दो", "sat": "ᱵᱟᱨ"},
    {"val": 3, "ta": "மூன்று", "ml": "മൂന്ന്", "te": "మూడు", "kn": "ಮೂರು", "hi": "तीन", "sat": "ᱯᱮ"},
    {"val": 4, "ta": "நான்கு", "ml": "നാല്", "te": "నాలుగు", "kn": "ನಾಲ್ಕು", "hi": "चार", "sat": "ᱯᱩᱱ"},
    {"val": 5, "ta": "ஐந்து", "ml": "അഞ്ച്", "te": "ఐదు", "kn": "ಐದು", "hi": "पाँच", "sat": "ᱢᱚᱬᱮ"},
]


def generate_numeracy_worksheet_pdf(
    output_path: Path,
    source_lang: str = "ta",
    target_lang: str = "ml",
    grade: int = 1,
) -> Path:
    """Generate bilingual counting and tracing worksheet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)

    src_font = get_font_for_language(source_lang)
    tgt_font = get_font_for_language(target_lang)

    content_top_y = draw_pedagogy_header(
        c,
        title=f"FLN Numeracy Worksheet (Grade {grade})",
        source_lang=source_lang,
        target_lang=target_lang,
        subtitle="Count the dots, trace the numbers, and learn the bilingual names",
    )

    # Student metadata header box
    meta_y = content_top_y - 2 * mm
    c.setFont("Helvetica-Bold", 8.5)
    c.setFillColor(COLOR_DARK)
    c.drawString(MARGIN, meta_y, "Student Name: __________________________")
    c.drawString(MARGIN + 90 * mm, meta_y, "Date: ____________")
    c.drawString(MARGIN + 140 * mm, meta_y, f"Grade: {grade}")

    row_start_y = meta_y - 10 * mm
    row_height = 32 * mm

    for idx, item in enumerate(NUMERAL_DATA):
        row_y = row_start_y - idx * row_height

        # Card container
        c.setFillColor(white)
        c.setStrokeColor(COLOR_BORDER)
        c.setLineWidth(0.8)
        c.roundRect(MARGIN, row_y, PRINTABLE_W, row_height - 3 * mm, 2 * mm, fill=1, stroke=1)

        # 1. Big numeral numeral box
        c.setFillColor(COLOR_TEAL)
        c.roundRect(MARGIN + 3 * mm, row_y + 4 * mm, 18 * mm, row_height - 11 * mm, 2 * mm, fill=1, stroke=0)
        c.setFont("Helvetica-Bold", 20)
        c.setFillColor(white)
        c.drawCentredString(MARGIN + 12 * mm, row_y + 9 * mm, str(item["val"]))

        # 2. Orange Dot counters
        c.setFillColor(COLOR_ORANGE)
        dot_start_x = MARGIN + 26 * mm
        for d in range(item["val"]):
            c.circle(dot_start_x + d * 8 * mm, row_y + (row_height - 3 * mm) / 2, 3 * mm, fill=1, stroke=0)

        # 3. Bilingual number words
        src_word = item.get(source_lang, str(item["val"]))
        tgt_word = item.get(target_lang, str(item["val"]))

        c.setFont(src_font, 12)
        c.setFillColor(COLOR_DARK)
        c.drawString(MARGIN + 80 * mm, row_y + (row_height - 3 * mm) / 2 + 2 * mm, src_word)

        c.setFont(tgt_font, 12)
        c.setFillColor(COLOR_TEAL)
        c.drawString(MARGIN + 80 * mm, row_y + 5 * mm, f"({tgt_word})")

        # 4. Tracing box
        trace_x = MARGIN + PRINTABLE_W - 45 * mm
        c.setStrokeColor(COLOR_BORDER)
        c.setLineCap(1)
        c.setDash(2, 2)
        c.rect(trace_x, row_y + 4 * mm, 40 * mm, row_height - 11 * mm, fill=0, stroke=1)
        c.setDash()

        c.setFont("Helvetica-Oblique", 14)
        c.setFillColor(COLOR_MUTED)
        c.drawCentredString(trace_x + 20 * mm, row_y + 9 * mm, f"{item['val']}  {item['val']}  {item['val']}")

    draw_pedagogy_footer(c, page_num=1, total_pages=1)
    c.showPage()
    c.save()

    logger.info(f"Numeracy Worksheet generated: {output_path}")
    return output_path


def generate_matching_worksheet_pdf(
    output_path: Path,
    source_lang: str = "ta",
    target_lang: str = "ml",
    grade: int = 1,
) -> Path:
    """Generate bilingual word-matching literacy worksheet."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(output_path), pagesize=A4)

    src_font = get_font_for_language(source_lang)
    tgt_font = get_font_for_language(target_lang)

    content_top_y = draw_pedagogy_header(
        c,
        title=f"FLN Literacy Word-Match (Grade {grade})",
        source_lang=source_lang,
        target_lang=target_lang,
        subtitle="Draw lines to match words with their translation",
    )

    items = SEED_ENTRIES[:5]
    left_items = items
    right_items = list(items)
    random.Random(42).shuffle(right_items)

    y_start = content_top_y - 20 * mm
    row_gap = 25 * mm

    for idx in range(len(items)):
        y = y_start - idx * row_gap
        l_item = left_items[idx]
        r_item = right_items[idx]

        # Left box (Source Language)
        c.setFillColor(white)
        c.setStrokeColor(COLOR_BORDER)
        c.roundRect(MARGIN + 10 * mm, y, 55 * mm, 16 * mm, 2 * mm, fill=1, stroke=1)
        c.setFont(src_font, 12)
        c.setFillColor(COLOR_DARK)
        c.drawCentredString(MARGIN + 37.5 * mm, y + 5 * mm, l_item.source_text)

        # Connector dot left
        c.setFillColor(COLOR_TEAL)
        c.circle(MARGIN + 68 * mm, y + 8 * mm, 2 * mm, fill=1, stroke=0)

        # Connector dot right
        c.circle(PAGE_W - MARGIN - 68 * mm, y + 8 * mm, 2 * mm, fill=1, stroke=0)

        # Right box (Target Language)
        c.setFillColor(white)
        c.setStrokeColor(COLOR_BORDER)
        c.roundRect(PAGE_W - MARGIN - 65 * mm, y, 55 * mm, 16 * mm, 2 * mm, fill=1, stroke=1)
        c.setFont(tgt_font, 12)
        c.setFillColor(COLOR_TEAL)
        c.drawCentredString(PAGE_W - MARGIN - 37.5 * mm, y + 5 * mm, r_item.target_text)

    draw_pedagogy_footer(c, page_num=1, total_pages=1)
    c.showPage()
    c.save()

    logger.info(f"Literacy Matching Worksheet generated: {output_path}")
    return output_path
