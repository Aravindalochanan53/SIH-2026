"""
Local Named Entity Recognition API Endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter
from pydantic import BaseModel, Field

from backend.app.services.ner_service import NERService

router = APIRouter(prefix="/api/local/ner", tags=["Local AI Named Entity Recognition"])


class NERExtractRequest(BaseModel):
    text: str = Field(..., description="Text from which to extract entities")


@router.post("/extract")
async def extract_entities(req: NERExtractRequest):
    """Extract named entities and token masking maps locally."""
    return NERService.extract_entities(req.text)
