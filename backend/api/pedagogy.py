"""
Pedagogy & PDF Generation API Router for TRANSLARA with MSSQL Record Tracking.
"""
import uuid
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from loguru import logger
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_optional_user
from backend.config import settings
from backend.database.models import User
from backend.database.repositories.chat_and_pedagogy_repo import PedagogyRepository
from backend.database.session import get_db
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
async def generate_flashcards(
    req: FlashcardGenerationRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Generate 2x4 A4 bilingual vocabulary flashcards and store record in MSSQL."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    entries = get_entries_for_pair(source_lang, target_lang)
    if req.category:
        filtered = [e for e in entries if e.category.lower() == req.category.lower()]
        if filtered:
            entries = filtered

    flashcard_id = f"fc_{uuid.uuid4().hex[:12]}"
    file_name = f"flashcards_{source_lang}_{target_lang}_{flashcard_id}.pdf"
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

    # Record in MSSQL
    try:
        pedagogy_repo = PedagogyRepository(db)
        pedagogy_repo.save_flashcard(
            flashcard_id=flashcard_id,
            deck_name=req.title or "Bilingual Vocabulary Flashcards",
            word=entries[0].source_text if entries else "Classroom Deck",
            translation=entries[0].target_text if entries else "Classroom Deck",
            source_language=source_lang,
            target_language=target_lang,
            category=req.category or "General",
            file_path=str(out_path),
            user_id=user.id if user else None,
        )
    except Exception:
        pass

    return PDFGenerationResponse(
        file_name=file_name,
        download_url=f"/api/pedagogy/download/{file_name}",
        page_count=1,
        source_lang=source_lang,
        target_lang=target_lang,
    )


@router.post("/numeracy", response_model=PDFGenerationResponse)
async def generate_numeracy(
    req: NumeracyWorksheetRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Generate bilingual numeracy counting & tracing worksheet and record in MSSQL."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    worksheet_id = f"ws_num_{uuid.uuid4().hex[:12]}"
    file_name = f"numeracy_g{req.grade}_{source_lang}_{target_lang}_{worksheet_id}.pdf"
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

    # Record in MSSQL
    try:
        pedagogy_repo = PedagogyRepository(db)
        pedagogy_repo.save_worksheet(
            worksheet_id=worksheet_id,
            title=f"FLN Numeracy Worksheet - Grade {req.grade}",
            grade=str(req.grade),
            subject="Numeracy",
            source_language=source_lang,
            target_language=target_lang,
            file_path=str(out_path),
            user_id=user.id if user else None,
        )
    except Exception:
        pass

    return PDFGenerationResponse(
        file_name=file_name,
        download_url=f"/api/pedagogy/download/{file_name}",
        page_count=1,
        source_lang=source_lang,
        target_lang=target_lang,
    )


@router.post("/literacy", response_model=PDFGenerationResponse)
async def generate_literacy(
    req: LiteracyWorksheetRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Generate bilingual word-matching literacy worksheet and record in MSSQL."""
    source_lang = req.source_lang.lower().strip()
    target_lang = req.target_lang.lower().strip()

    worksheet_id = f"ws_lit_{uuid.uuid4().hex[:12]}"
    file_name = f"literacy_g{req.grade}_{source_lang}_{target_lang}_{worksheet_id}.pdf"
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

    # Record in MSSQL
    try:
        pedagogy_repo = PedagogyRepository(db)
        pedagogy_repo.save_worksheet(
            worksheet_id=worksheet_id,
            title=f"FLN Literacy Worksheet - Grade {req.grade}",
            grade=str(req.grade),
            subject="Literacy",
            source_language=source_lang,
            target_language=target_lang,
            file_path=str(out_path),
            user_id=user.id if user else None,
        )
    except Exception:
        pass

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
    clean_name = Path(file_name).name
    target_path = (Path(settings.pdf_output_dir) / clean_name).resolve()

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
