"""
Database package for TRANSLARA.
Exports Base, engine, SessionLocal, get_db, init_db, and ORM models.
"""
from backend.database.base import Base
from backend.database.connection import check_db_health, engine, init_db
from backend.database.session import SessionLocal, get_db
from backend.database.models import (
    ChatMessage,
    ChatSession,
    ClassroomPhrase,
    EntityRecord,
    Flashcard,
    Language,
    ModelUsage,
    Translation,
    TranslationHistory,
    User,
    VideoJob,
    Worksheet,
)

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db",
    "init_db",
    "check_db_health",
    "User",
    "Language",
    "Translation",
    "TranslationHistory",
    "ChatSession",
    "ChatMessage",
    "VideoJob",
    "Worksheet",
    "Flashcard",
    "ClassroomPhrase",
    "EntityRecord",
    "ModelUsage",
]
