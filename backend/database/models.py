"""
SQLAlchemy ORM Data Models for TRANSLARA.
Fully compatible with Microsoft SQL Server (MSSQL) using Unicode-safe datatypes (NVARCHAR, UnicodeText).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Unicode,
    UnicodeText,
)
from sqlalchemy.orm import relationship

from backend.database.base import Base


def _utc_now():
    return datetime.now(timezone.utc)


def _gen_uuid():
    return str(uuid.uuid4())


class User(Base):
    """User account model for authentication, role management, and activity tracking."""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Unicode(150), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="teacher", nullable=False)  # 'teacher', 'admin'
    preferred_source_lang = Column(String(10), default="ta")
    preferred_target_lang = Column(String(10), default="ml")
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)

    # Relationships
    translation_history = relationship("TranslationHistory", back_populates="user", cascade="all, delete-orphan")
    chat_sessions = relationship("ChatSession", back_populates="user", cascade="all, delete-orphan")
    video_jobs = relationship("VideoJob", back_populates="user")
    worksheets = relationship("Worksheet", back_populates="user")
    flashcards = relationship("Flashcard", back_populates="user")


class Language(Base):
    """Registered Indian languages registry."""
    __tablename__ = "languages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), unique=True, index=True, nullable=False)
    name = Column(Unicode(100), nullable=False)
    native_name = Column(Unicode(100), nullable=False)
    script = Column(Unicode(50), nullable=False)
    region = Column(Unicode(100), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)


class Translation(Base):
    """Verified and cached translation records."""
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_language = Column(String(10), index=True, nullable=False)
    target_language = Column(String(10), index=True, nullable=False)
    source_text = Column(UnicodeText, nullable=False)
    target_text = Column(UnicodeText, nullable=False)
    engine = Column(String(50), default="indictrans2")
    is_verified = Column(Boolean, default=False, nullable=False)
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=_utc_now, nullable=False)


class TranslationHistory(Base):
    """User and session translation event log."""
    __tablename__ = "translation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    session_id = Column(String(100), index=True, nullable=True)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    source_text = Column(UnicodeText, nullable=False)
    translated_text = Column(UnicodeText, nullable=False)
    input_type = Column(String(20), default="text", nullable=False)  # 'text', 'voice', 'video'
    model_used = Column(String(100), default="TRANSLARA-NMT-v1")
    model_version = Column(String(50), default="1.0")
    latency_ms = Column(Float, default=0.0)
    offline_used = Column(Boolean, default=False)
    validation_passed = Column(Boolean, default=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    user = relationship("User", back_populates="translation_history")


class ChatSession(Base):
    """Conversational sessions with TRANSLARA AI Teaching Assistant."""
    __tablename__ = "chat_sessions"

    id = Column(String(36), primary_key=True, default=_gen_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    title = Column(Unicode(255), default="AI Teaching Assistant Session", nullable=False)
    language = Column(String(10), default="ta", nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    updated_at = Column(DateTime, default=_utc_now, onupdate=_utc_now, nullable=False)

    user = relationship("User", back_populates="chat_sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan", order_by="ChatMessage.created_at")


class ChatMessage(Base):
    """Individual messages inside a chat session."""
    __tablename__ = "chat_messages"

    id = Column(String(36), primary_key=True, default=_gen_uuid, index=True)
    session_id = Column(String(36), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(20), nullable=False)  # 'user', 'assistant', 'system'
    message = Column(UnicodeText, nullable=False)
    language = Column(String(10), default="ta", nullable=False)
    model_used = Column(String(100), default="TRANSLARA-Edu")
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    session = relationship("ChatSession", back_populates="messages")


class VideoJob(Base):
    """Background asynchronous video dubbing and subtitle generation tasks."""
    __tablename__ = "video_jobs"

    id = Column(String(100), primary_key=True, default=_gen_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    original_filename = Column(Unicode(255), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    status = Column(String(50), default="queued", nullable=False)  # 'queued', 'processing', 'completed', 'failed'
    progress = Column(Float, default=0.0)
    input_path = Column(String(500), nullable=True)
    output_path = Column(String(500), nullable=True)
    transcript_path = Column(String(500), nullable=True)
    subtitle_path = Column(String(500), nullable=True)
    error_message = Column(UnicodeText, nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
    completed_at = Column(DateTime, nullable=True)

    user = relationship("User", back_populates="video_jobs")


class Worksheet(Base):
    """Generated bilingual numeracy and literacy worksheet metadata."""
    __tablename__ = "worksheets"

    id = Column(String(100), primary_key=True, default=_gen_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(Unicode(255), nullable=False)
    grade = Column(String(20), default="1", nullable=False)
    subject = Column(Unicode(50), default="FLN", nullable=False)
    language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    file_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    user = relationship("User", back_populates="worksheets")


class Flashcard(Base):
    """Generated bilingual flashcard deck records."""
    __tablename__ = "flashcards"

    id = Column(String(100), primary_key=True, default=_gen_uuid, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    deck_name = Column(Unicode(100), default="FLN Classroom Deck", nullable=False)
    word = Column(Unicode(255), nullable=False)
    translation = Column(Unicode(255), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    category = Column(Unicode(50), default="General", nullable=False)
    file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)

    user = relationship("User", back_populates="flashcards")


class ClassroomPhrase(Base):
    """High-frequency educational and classroom phrases for instant offline access."""
    __tablename__ = "classroom_phrases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), index=True, nullable=False)
    source_language = Column(String(10), index=True, nullable=False)
    target_language = Column(String(10), index=True, nullable=False)
    source_text = Column(UnicodeText, nullable=False)
    target_text = Column(UnicodeText, nullable=False)
    audio_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)


class EntityRecord(Base):
    """Proper nouns, student roster names, and village gazetteers for entity locking."""
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(Unicode(255), index=True, nullable=False)
    kind = Column(String(50), default="PERSON", nullable=False)
    language = Column(String(10), default="all", nullable=False)
    phonetic_hint = Column(Unicode(255), nullable=True)
    created_at = Column(DateTime, default=_utc_now, nullable=False)


class ModelUsage(Base):
    """Operational telemetry and AI model usage metrics."""
    __tablename__ = "model_usage"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, nullable=True)
    service_name = Column(String(50), nullable=False)  # 'asr', 'nmt', 'tts', 'chat'
    model_name = Column(String(100), nullable=False)
    character_or_token_count = Column(Integer, default=0)
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=_utc_now, nullable=False)
