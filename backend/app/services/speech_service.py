"""
TRANSLARA — Local Speech-to-Text Service.

Executes speech recognition locally using Faster-Whisper / CTranslate2 INT8 model.
"""
from __future__ import annotations

from typing import Any, Dict, Optional
from backend.app.models.inference import infer_asr_local
from backend.ml_engine.audio_processor import AudioProcessor


class SpeechService:
    """
    Service layer for local ASR transcription.
    """

    @staticmethod
    async def transcribe_audio_bytes(
        audio_bytes: bytes,
        language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Normalize audio and transcribe locally."""
        pcm16 = AudioProcessor.normalize_pcm16(audio_bytes)
        return await infer_asr_local(pcm16, language=language)
