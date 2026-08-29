"""
Translation & Entity Management API Endpoints for TRANSLARA.
Routes through the modular TRANSLARA AI translation engine.
"""
from __future__ import annotations

import time
from fastapi import APIRouter, Depends, HTTPException
from loguru import logger
from sqlalchemy.orm import Session

from backend.ai.translation.registry import get_translation_engine
from backend.ai.validators.translation_validator import TranslationValidator
from backend.cache.database import get_db
from backend.cache.models import EntityRecord
from backend.exceptions import UnsupportedLanguagePairError
from backend.ml_engine.languages import is_pair_supported
from backend.schemas import (
    EntityCreateRequest,
    EntityResponse,
    LockedEntity,
    TranslationRequest,
    TranslationResponse,
)

router = APIRouter(prefix="/api", tags=["Translation"])


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(req: TranslationRequest):
    """
    Perform Generic SOURCE -> TARGET translation with deterministic Entity Locking and quality validation.
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


@router.post("/entities", response_model=EntityResponse)
async def create_entity(req: EntityCreateRequest, db: Session = Depends(get_db)):
    """
    Register a new proper noun or terminology into the persistent SQLite Entity Registry.
    """
    existing = (
        db.query(EntityRecord)
        .filter(
            EntityRecord.text == req.text,
            EntityRecord.language == req.language,
        )
        .first()
    )

    if existing:
        return EntityResponse(
            id=existing.id,
            text=existing.text,
            language=existing.language,
            entity_type=existing.entity_type,
            phonetic_hint=existing.phonetic_hint,
            preserve_mode=existing.preserve_mode,
            domain=existing.domain,
        )

    record = EntityRecord(
        text=req.text,
        language=req.language,
        entity_type=req.entity_type,
        phonetic_hint=req.phonetic_hint,
        preserve_mode=req.preserve_mode,
        domain=req.domain,
    )
    db.add(record)
    db.commit()
    db.refresh(record)

    return EntityResponse(
        id=record.id,
        text=record.text,
        language=record.language,
        entity_type=record.entity_type,
        phonetic_hint=record.phonetic_hint,
        preserve_mode=record.preserve_mode,
        domain=record.domain,
    )
