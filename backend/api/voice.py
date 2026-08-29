"""
Voice & Speech API Endpoints for TRANSLARA.
Complements real-time WebSocket /ws/live-stream with REST audio synthesis & verification.
"""
from __future__ import annotations

import base64
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import Optional

from backend.ai.tts.indic_tts_provider import get_tts_engine
from backend.ai.asr.faster_whisper_provider import FasterWhisperProvider
from backend.schemas import SubsystemStatus

router = APIRouter(prefix="/api/voice", tags=["Voice"])


class VoiceSynthesizeRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Text to synthesize to speech")
    target_language: str = Field(default="ml", description="Target language code e.g. ml, ta, te, kn, hi")
    speaker_gender: str = Field(default="female", description="female or male")


class VoiceSynthesizeResponse(BaseModel):
    success: bool
    text: str
    target_language: str
    sample_rate: int = 16000
    audio_base64: str
    format: str = "pcm_s16le"


class VoiceStatusResponse(BaseModel):
    microphone_support: bool = True
    websocket_endpoint: str = "/ws/live-stream"
    sample_rate: int = 16000
    channels: int = 1
    chunk_size_ms: int = 200
    status: str = "ready"


@router.get("/status", response_model=VoiceStatusResponse)
async def get_voice_status():
    """Get live audio streaming configuration and WebSocket endpoints."""
    return VoiceStatusResponse()


@router.post("/synthesize", response_model=VoiceSynthesizeResponse)
async def synthesize_speech(req: VoiceSynthesizeRequest):
    """Synthesize speech audio PCM bytes for translated text."""
    try:
        tts = get_tts_engine()
        chunks = []
        async for chunk in tts.synthesize_stream(req.text, req.target_language):
            chunks.append(chunk)

        full_pcm = b"".join(chunks)
        b64_audio = base64.b64encode(full_pcm).decode("utf-8")

        return VoiceSynthesizeResponse(
            success=True,
            text=req.text,
            target_language=req.target_language,
            sample_rate=16000,
            audio_base64=b64_audio,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Voice synthesis failed: {str(e)}")
