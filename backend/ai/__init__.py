"""
TRANSLARA AI Multilingual Engine.
Modular multilingual translation, speech recognition, entity locking, and synthesis.
"""
from backend.ai.language_detection.detector import LanguageDetector, get_language_detector
from backend.ai.model_manager import ModelManager, get_model_manager
from backend.ai.ner.entity_lock import EntityLock, get_entity_lock
from backend.ai.orchestration.pipeline import RealtimePipeline, get_realtime_pipeline
from backend.ai.translation.registry import TranslationEngine, get_translation_engine
from backend.ai.validators.translation_validator import TranslationValidator

__all__ = [
    "LanguageDetector",
    "get_language_detector",
    "ModelManager",
    "get_model_manager",
    "EntityLock",
    "get_entity_lock",
    "RealtimePipeline",
    "get_realtime_pipeline",
    "TranslationEngine",
    "get_translation_engine",
    "TranslationValidator",
]
