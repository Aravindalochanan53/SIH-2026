"""
SQLAlchemy ORM Data Models for TRANSLARA.
"""
from __future__ import annotations

from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text, Unicode, UnicodeText
from backend.cache.database import Base


def _utc_now():
    return datetime.now(timezone.utc)


class Phrase(Base):
    """
    Multilingual verified classroom & educational phrases for offline fallback.
    """
    __tablename__ = "phrases"

    id = Column(String(64), primary_key=True, index=True)
    category = Column(String(64), index=True, nullable=False, default="general")
    source_language = Column(String(10), index=True, nullable=False, default="ta")
    target_language = Column(String(10), index=True, nullable=False, default="ml")
    source_text = Column(UnicodeText, nullable=False)
    target_text = Column(UnicodeText, nullable=False)
    pronunciation = Column(UnicodeText, default="")
    verified = Column(Boolean, default=False, nullable=False)
    translation_status = Column(String(32), default="NEEDS_REVIEW", nullable=False)
    audio_path = Column(String(256), nullable=True)

    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)


class EntityRecord(Base):
    """
    Persistent store for student roster, proper nouns, and village gazetteers.
    """
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(Unicode(128), unique=True, index=True, nullable=False)
    kind = Column(String(32), nullable=False, default="PERSON")
    language = Column(String(10), nullable=True, default="all")
    phonetic_hint = Column(Unicode(128), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)


class AudioCache(Base):
    """Pre-rendered TTS audio chunks for instant zero-latency playback."""
    __tablename__ = "audio_cache"

    id = Column(String(64), primary_key=True)
    phrase_id = Column(String(64), index=True, nullable=False)
    language = Column(String(10), nullable=False)
    file_path = Column(String(256), nullable=False)
    duration_ms = Column(Integer, default=0)
    created_at = Column(DateTime, default=_utc_now, nullable=False)


class CacheMetadata(Base):
    """Tracks cache versioning and seed timestamps."""
    __tablename__ = "cache_metadata"

    key = Column(String(64), primary_key=True)
    value = Column(String(256), nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)
