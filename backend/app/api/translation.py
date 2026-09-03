"""
Local Translation API Endpoints.
"""
from __future__ import annotations

from typing import List, Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from backend.app.services.translation_service import TranslationService

router = APIRouter(prefix="/api/local/translation", tags=["Local AI Translation"])


class LocalTranslateRequest(BaseModel):
    text: str = Field(..., description="Source text to translate locally")
    source_lang: str = Field(default="ta", description="Source language code (e.g. 'ta', 'hi', 'en')")
    target_lang: str = Field(default="ml", description="Target language code (e.g. 'ml', 'te', 'sat')")


class LocalBatchTranslateRequest(BaseModel):
    texts: List[str] = Field(..., description="List of source texts")
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="ml")


@router.post("/translate")
async def translate_text(req: LocalTranslateRequest):
    """Translate text using 100% local translation models without any cloud AI APIs."""
    try:
        return await TranslationService.translate_text(
            text=req.text,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local translation error: {str(e)}")


@router.post("/batch")
async def translate_batch(req: LocalBatchTranslateRequest):
    """Batch translate texts locally."""
    try:
        return await TranslationService.translate_batch(
            texts=req.texts,
            source_lang=req.source_lang,
            target_lang=req.target_lang,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local batch translation error: {str(e)}")
