"""
Pedagogy & PDF Generation API Router for TRANSLARA.
"""
import uuid
from pathlib import Path
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from loguru import logger

from backend.config import settings
from backend.pedagogy.content_bank import get_entries_for_pair
from backend.pedagogy.flashcard_generator import generate_flashcard_pdf
from backend.pedagogy.worksheet_generator import (
    generate_matching_worksheet_pdf,
    generate_numeracy_worksheet_pdf,
)
from backend.schemas import (
    FlashcardGenerationRequest,
    LiteracyWorksheetRequest,
    NumeracyWorksheetRequest,
    PDFGenerationResponse,
)

router = APIRouter(prefix="/api/pedagogy", tags=["Pedagogy"])


@router.post("/flashcards", response_model=PDFGenerationResponse)
async def generate_flashcards(req: FlashcardGenerationRequest):
    """Generate 2x4 A4 bilingual vocabulary flashcards."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    entries = get_entries_for_pair(source_lang, target_lang)
    if req.category:
        filtered = [e for e in entries if e.category.lower() == req.category.lower()]
        if filtered:
            entries = filtered

    file_name = f"flashcards_{source_lang}_{target_lang}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = Path(settings.pdf_output_dir) / file_name

    try:
        generate_flashcard_pdf(
            entries=entries,
            source_lang=source_lang,
            target_lang=target_lang,
            output_path=out_path,
            title=req.title or "Bilingual Vocabulary Flashcards",
        )
    except Exception as e:
        logger.error(f"Failed to generate flashcard PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation error: {e}")

    return PDFGenerationResponse(
        file_name=file_name,
        download_url=f"/api/pedagogy/download/{file_name}",
        page_count=1,
        source_lang=source_lang,
        target_lang=target_lang,
    )


@router.post("/numeracy", response_model=PDFGenerationResponse)
async def generate_numeracy(req: NumeracyWorksheetRequest):
    """Generate bilingual numeracy counting & tracing worksheet."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    file_name = f"numeracy_g{req.grade}_{source_lang}_{target_lang}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = Path(settings.pdf_output_dir) / file_name

    try:
        generate_numeracy_worksheet_pdf(
            output_path=out_path,
            source_lang=source_lang,
            target_lang=target_lang,
            grade=req.grade,
        )
    except Exception as e:
        logger.error(f"Failed to generate numeracy PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation error: {e}")

    return PDFGenerationResponse(
        file_name=file_name,
        download_url=f"/api/pedagogy/download/{file_name}",
        page_count=1,
        source_lang=source_lang,
        target_lang=target_lang,
    )


@router.post("/literacy", response_model=PDFGenerationResponse)
async def generate_literacy(req: LiteracyWorksheetRequest):
    """Generate bilingual word-matching literacy worksheet."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    file_name = f"literacy_g{req.grade}_{source_lang}_{target_lang}_{uuid.uuid4().hex[:8]}.pdf"
    out_path = Path(settings.pdf_output_dir) / file_name

    try:
        generate_matching_worksheet_pdf(
            output_path=out_path,
            source_lang=source_lang,
            target_lang=target_lang,
            grade=req.grade,
        )
    except Exception as e:
        logger.error(f"Failed to generate literacy PDF: {e}")
        raise HTTPException(status_code=500, detail=f"PDF Generation error: {e}")

    return PDFGenerationResponse(
        file_name=file_name,
        download_url=f"/api/pedagogy/download/{file_name}",
        page_count=1,
        source_lang=source_lang,
        target_lang=target_lang,
    )


@router.get("/download/{file_name}")
async def download_pdf(file_name: str):
    """Secure PDF download endpoint with path traversal protection."""
    # Sanitize filename
    clean_name = Path(file_name).name
    target_path = (Path(settings.pdf_output_dir) / clean_name).resolve()

    # Path traversal validation
    base_dir = Path(settings.pdf_output_dir).resolve()
    if not str(target_path).startswith(str(base_dir)):
        raise HTTPException(status_code=403, detail="Forbidden access path")

    if not target_path.exists():
        raise HTTPException(status_code=404, detail="Requested PDF file not found")

    return FileResponse(
        path=str(target_path),
        filename=clean_name,
        media_type="application/pdf",
    )
