"""
Translation & Entity Management API Endpoints for TRANSLARA.
Routes through the modular TRANSLARA AI translation engine and stores history in MSSQL.
"""
from __future__ import annotations

import time
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from loguru import logger
from sqlalchemy.orm import Session

from backend.ai.translation.registry import get_translation_engine
from backend.auth.dependencies import get_current_user, get_optional_user
from backend.database.models import EntityRecord, TranslationHistory, User
from backend.database.repositories.translation_repo import TranslationRepository
from backend.database.session import get_db
from backend.ml_engine.languages import is_pair_supported
from backend.schemas import (
    EntityCreateRequest,
    EntityResponse,
    LockedEntity,
    TranslationRequest,
    TranslationResponse,
)

router = APIRouter(tags=["Translation"])


# --- Translation Endpoints ---

@router.post("/api/translate", response_model=TranslationResponse)
@router.post("/api/translate/text", response_model=TranslationResponse)
async def translate_text(
    req: TranslationRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Perform Generic SOURCE -> TARGET translation with deterministic Entity Locking,
    quality validation, and persistence to MSSQL translation history.
    """
    src = req.source_lang or req.source_language or "ta"
    tgt = req.target_lang or req.target_language or "ml"
    source_lang = src.lower().strip()
    target_lang = tgt.lower().strip()

    if not is_pair_supported(source_lang, target_lang):
        return TranslationResponse(
            success=False,
            original_text=req.text,
            translation=None,
            source_language=source_lang,
            target_language=target_lang,
            engine="unsupported",
            offline=False,
            pivot_translation=False,
            latency_ms=0.0,
            error=f"Translation for {source_lang.upper()} -> {target_lang.upper()} is not supported.",
        )

    engine = get_translation_engine()

    try:
        res = await engine.translate(
            text=req.text,
            source_lang=source_lang,
            target_lang=target_lang,
        )
    except Exception as e:
        logger.error(f"Translation API error: {e}")
        return TranslationResponse(
            success=False,
            original_text=req.text,
            translation=None,
            source_language=source_lang,
            target_language=target_lang,
            engine="error",
            offline=False,
            pivot_translation=False,
            latency_ms=0.0,
            error=f"Translation provider unavailable: {str(e)}",
        )

    # Detect entities for API response metadata
    entities = engine.entity_lock.detect_entities(req.text)
    locked_schemas = [
        LockedEntity(
            text=e.text,
            type=e.type,
            start=e.start_char,
            end=e.end_char,
            phonetic_hint=None,
        )
        for e in entities
    ]

    # Save to MSSQL Translation History
    try:
        repo = TranslationRepository(db)
        repo.save_history(
            user_id=user.id if user else None,
            source_language=source_lang,
            target_language=target_lang,
            source_text=req.text,
            translated_text=res.text or "",
            input_type="text",
            model_used=res.backend,
            model_version="1.0",
            latency_ms=round(res.latency_ms, 2),
            offline_used=res.backend.startswith("offline"),
            validation_passed=True,
        )
    except Exception as db_err:
        logger.warning(f"Could not persist translation history to MSSQL: {db_err}")

    return TranslationResponse(
        success=True,
        original_text=req.text,
        translation=res.text,
        source_language=source_lang,
        target_language=target_lang,
        engine=res.backend,
        offline=res.backend.startswith("offline"),
        pivot_translation=res.pivot_used,
        latency_ms=round(res.latency_ms, 2),
        warning="; ".join(res.warnings) if res.warnings else None,
        detected_lang=res.detected_lang or res.source_lang,
        entities_locked=locked_schemas,
    )


# --- Translation History Endpoints ---

@router.get("/api/translation/history")
async def get_translation_history(
    limit: int = 50,
    offset: int = 0,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Retrieve translation history from MSSQL.
    Returns the authenticated user's records or all if admin.
    """
    repo = TranslationRepository(db)
    is_admin = (user.role == "admin") if user else False
    user_id = user.id if user else None

    records = repo.get_history_by_user(user_id=user_id, is_admin=is_admin, limit=limit, offset=offset)
    return [
        {
            "id": r.id,
            "user_id": r.user_id,
            "source_language": r.source_language,
            "target_language": r.target_language,
            "source_text": r.source_text,
            "translated_text": r.translated_text,
            "input_type": r.input_type,
            "model_used": r.model_used,
            "model_version": r.model_version,
            "latency_ms": r.latency_ms,
            "offline_used": r.offline_used,
            "validation_passed": r.validation_passed,
            "created_at": r.created_at.isoformat() if r.created_at else None,
        }
        for r in records
    ]


@router.get("/api/translation/history/{history_id}")
async def get_translation_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Retrieve a single translation history record by ID."""
    repo = TranslationRepository(db)
    record = repo.get_history_by_id(history_id)
    if not record:
        raise HTTPException(status_code=404, detail="Translation history record not found")

    if user and user.role != "admin" and record.user_id != user.id:
        raise HTTPException(status_code=403, detail="Not authorized to access this record")

    return {
        "id": record.id,
        "user_id": record.user_id,
        "source_language": record.source_language,
        "target_language": record.target_language,
        "source_text": record.source_text,
        "translated_text": record.translated_text,
        "input_type": record.input_type,
        "model_used": record.model_used,
        "latency_ms": record.latency_ms,
        "offline_used": record.offline_used,
        "created_at": record.created_at.isoformat() if record.created_at else None,
    }


@router.delete("/api/translation/history/{history_id}")
async def delete_translation_history_item(
    history_id: int,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Delete a translation history record by ID."""
    repo = TranslationRepository(db)
    is_admin = (user.role == "admin") if user else False
    user_id = user.id if user else None

    deleted = repo.delete_history_by_id(history_id=history_id, user_id=user_id, is_admin=is_admin)
    if not deleted:
        raise HTTPException(status_code=404, detail="Record not found or not authorized to delete")

    return {"status": "deleted", "id": history_id}


# --- Entity Registry Endpoints ---

@router.post("/api/entities", response_model=EntityResponse)
async def create_entity(req: EntityCreateRequest, db: Session = Depends(get_db)):
    """Register a new proper noun or terminology into the MSSQL Entity Registry."""
    existing = db.query(EntityRecord).filter(EntityRecord.name == req.name).first()
    if existing:
        return EntityResponse(
            id=existing.id,
            name=existing.name,
            kind=existing.kind,
            phonetic_hint=existing.phonetic_hint,
        )

    record = EntityRecord(
        name=req.name,
        kind=req.kind,
        phonetic_hint=req.phonetic_hint,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EntityResponse(
        id=record.id,
        name=record.name,
        kind=record.kind,
        phonetic_hint=record.phonetic_hint,
    )
