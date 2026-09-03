"""
Local AI Observability & Model Status API Endpoints.
"""
from __future__ import annotations

from fastapi import APIRouter
from backend.app.models.model_loader import get_local_model_manager

router = APIRouter(prefix="/api/local/ai", tags=["Local AI Status & Models"])


@router.get("/status")
async def get_ai_status():
    """Returns runtime status of all locally loaded AI models."""
    mgr = get_local_model_manager()
    return mgr.get_status()


@router.get("/models")
async def list_models():
    """Lists locally available trained model artifacts in trained_models/."""
    mgr = get_local_model_manager()
    return {
        "device": mgr.device,
        "models": {
            "translation": {
                "name": "TRANSLARA-NMT-Local-v1",
                "location": str(mgr.translation_model_dir),
                "type": "Neural Grammar & CTranslate2 Transformer",
                "status": mgr._status.get("translation"),
            },
            "asr": {
                "name": "TRANSLARA-ASR-Local-v1",
                "location": str(mgr.asr_model_dir),
                "type": "Faster-Whisper INT8 Acoustic Model",
                "status": mgr._status.get("asr"),
            },
            "ner": {
                "name": "TRANSLARA-NER-Shield-v1",
                "location": str(mgr.ner_model_dir),
                "type": "Multilingual Gazetteer & Entity Shield",
                "status": mgr._status.get("ner"),
            },
            "tts": {
                "name": "TRANSLARA-TTS-Local-v1",
                "location": str(mgr.tts_model_dir),
                "type": "Chunked Acoustic Synthesizer",
                "status": mgr._status.get("tts"),
            },
        },
        "cloud_apis_used": False,
        "offline_inference": True,
    }
