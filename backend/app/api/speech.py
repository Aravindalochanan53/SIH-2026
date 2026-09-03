"""
Local Speech Recognition API Endpoints.
"""
from __future__ import annotations

from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from backend.app.services.speech_service import SpeechService

router = APIRouter(prefix="/api/local/speech", tags=["Local AI Speech Recognition"])


@router.post("/transcribe")
async def transcribe_audio(
    file: UploadFile = File(...),
    language: Optional[str] = Form(None),
):
    """Transcribe uploaded audio locally using Faster-Whisper / INT8 acoustic model."""
    try:
        content = await file.read()
        return await SpeechService.transcribe_audio_bytes(content, language=language)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Local ASR error: {str(e)}")
