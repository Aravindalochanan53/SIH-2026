"""
TRANSLARA Local AI Services Layer.
"""
from backend.app.services.translation_service import TranslationService
from backend.app.services.speech_service import SpeechService
from backend.app.services.ner_service import NERService

__all__ = ["TranslationService", "SpeechService", "NERService"]
