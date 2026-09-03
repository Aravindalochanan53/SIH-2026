"""
TRANSLARA Local AI API Routers.
"""
from backend.app.api.translation import router as translation_router
from backend.app.api.speech import router as speech_router
from backend.app.api.ner import router as ner_router
from backend.app.api.ai import router as ai_router

__all__ = [
    "translation_router",
    "speech_router",
    "ner_router",
    "ai_router",
]
