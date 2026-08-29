"""
SQLAlchemy ORM Data Models for TRANSLARA.
Stores relational entities for MSSQL / SQLite storage.
"""
from __future__ import annotations

import datetime
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from backend.database.connection import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    username = Column(String(100), unique=True, index=True, nullable=False)
    role = Column(String(50), default="teacher")  # 'teacher', 'admin', 'student'
    preferred_source_lang = Column(String(10), default="ta")
    preferred_target_lang = Column(String(10), default="ml")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Language(Base):
    __tablename__ = "languages"

    code = Column(String(10), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    native_name = Column(String(100), nullable=False)
    script = Column(String(50), nullable=False)
    region = Column(String(100), nullable=False)
    is_active = Column(Boolean, default=True)


class Translation(Base):
    __tablename__ = "translations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    source_language = Column(String(10), index=True, nullable=False)
    target_language = Column(String(10), index=True, nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    engine = Column(String(50), default="indictrans2")
    is_verified = Column(Boolean, default=False)
    category = Column(String(50), default="general")
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class TranslationHistory(Base):
    __tablename__ = "translation_history"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(String(100), index=True, nullable=True)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    source_text = Column(Text, nullable=False)
    translated_text = Column(Text, nullable=False)
    mode = Column(String(20), default="text")  # 'text', 'voice', 'video', 'chat'
    latency_ms = Column(Float, default=0.0)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ClassroomPhrase(Base):
    __tablename__ = "classroom_phrases"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    category = Column(String(50), index=True, nullable=False)  # 'greetings', 'instructions', 'fln_math', etc.
    source_language = Column(String(10), index=True, nullable=False)
    target_language = Column(String(10), index=True, nullable=False)
    source_text = Column(Text, nullable=False)
    target_text = Column(Text, nullable=False)
    audio_path = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class EntityRecord(Base):
    __tablename__ = "entities"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), index=True, nullable=False)
    kind = Column(String(50), default="PERSON")  # PERSON, LOCATION, VILLAGE, NUMBER, MATH
    language = Column(String(10), default="all")
    phonetic_hint = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class VideoJob(Base):
    __tablename__ = "video_jobs"

    id = Column(String(100), primary_key=True, index=True)
    filename = Column(String(255), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    status = Column(String(50), default="PENDING")  # PENDING, PROCESSING, COMPLETED, FAILED
    progress = Column(Float, default=0.0)
    original_video_url = Column(String(500), nullable=True)
    translated_video_url = Column(String(500), nullable=True)
    subtitles_srt_url = Column(String(500), nullable=True)
    subtitles_vtt_url = Column(String(500), nullable=True)
    transcript_url = Column(String(500), nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)


class ChatHistory(Base):
    __tablename__ = "chat_history"

    id = Column(String(100), primary_key=True, index=True)
    sender = Column(String(20), nullable=False)  # 'user', 'assistant'
    text = Column(Text, nullable=False)
    language = Column(String(10), nullable=False)
    translated_text = Column(Text, nullable=True)
    target_language = Column(String(10), nullable=True)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)


class Worksheet(Base):
    __tablename__ = "worksheets"

    id = Column(String(100), primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    grade = Column(String(20), nullable=False)
    subject = Column(String(50), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    pdf_path = Column(String(500), nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class Flashcard(Base):
    __tablename__ = "flashcards"

    id = Column(String(100), primary_key=True, index=True)
    deck_name = Column(String(100), index=True, default="FLN Classroom Deck")
    word = Column(String(255), nullable=False)
    translation = Column(String(255), nullable=False)
    source_language = Column(String(10), nullable=False)
    target_language = Column(String(10), nullable=False)
    category = Column(String(50), default="General")
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
