"""
Pydantic Schemas and Data Models for TRANSLARA.
"""
from __future__ import annotations

from enum import Enum
from typing import Any, Optional
from pydantic import BaseModel, Field


# --- Enums ---

class LanguageCode(str, Enum):
    TAMIL = "ta"
    TELUGU = "te"
    KANNADA = "kn"
    MALAYALAM = "ml"
    HINDI = "hi"
    SANTHALI = "sat"
    HO = "hoc"
    MUNDARI = "unr"
    BENGALI = "bn"
    MARATHI = "mr"
    AUTO = "auto"


class EntityType(str, Enum):
    PERSON = "PERSON"
    LOCATION = "LOCATION"
    VILLAGE = "VILLAGE"
    NUMBER = "NUMBER"
    DATE = "DATE"
    TIME = "TIME"
    MATH = "MATH"
    ORGANIZATION = "ORGANIZATION"
    CURRICULUM_TERM = "CURRICULUM_TERM"


class SubsystemStatus(str, Enum):
    READY = "ready"
    DEGRADED = "degraded"
    MOCK = "mock"
    UNAVAILABLE = "unavailable"


# --- Entity Models ---

class LockedEntity(BaseModel):
    text: str
    type: EntityType
    start: int = 0
    end: int = 0
    phonetic_hint: Optional[str] = None


class EntityCreateRequest(BaseModel):
    name: str = Field(..., min_length=1, description="Name of person, village, or term")
    kind: EntityType = Field(default=EntityType.PERSON)
    phonetic_hint: Optional[str] = None


class EntityResponse(BaseModel):
    id: int
    name: str
    kind: EntityType
    phonetic_hint: Optional[str] = None


# --- Translation & Pipeline Models ---

class TranslationRequest(BaseModel):
    text: str = Field(..., min_length=1, description="Source text to translate")
    source_language: Optional[str] = Field(default="ta", description="Source language code e.g. ta, te, kn, ml, hi, sat")
    target_language: Optional[str] = Field(default="ml", description="Target language code e.g. ta, te, kn, ml, hi, sat")
    source_lang: Optional[str] = Field(default=None, description="Alias for source_language")
    target_lang: Optional[str] = Field(default=None, description="Alias for target_language")


class TranslationResponse(BaseModel):
    success: bool = True
    original_text: str
    translation: Optional[str] = None
    source_language: str
    target_language: str
    engine: str = "indictrans2"
    offline: bool = False
    pivot_translation: bool = False
    latency_ms: float = 0.0
    error: Optional[str] = None
    warning: Optional[str] = None
    detected_lang: Optional[str] = None
    entities_locked: list[LockedEntity] = Field(default_factory=list)


class PipelineResultSchema(BaseModel):
    transcript: str
    translation: str
    source_lang: str
    target_lang: str
    detected_lang: Optional[str] = None
    entities_locked: list[LockedEntity] = Field(default_factory=list)
    stage_latencies_ms: dict[str, float] = Field(default_factory=dict)
    total_latency_ms: float = 0.0
    confidence: float = 1.0
    warning: Optional[str] = None
    used_offline_fallback: bool = False
    error: Optional[str] = None


# --- Language Registry & Capability Models ---

class LanguageDetail(BaseModel):
    code: str
    name: str
    native_name: str
    region: str
    script: str
    asr_supported: bool
    translation_supported: bool
    tts_supported: bool
    offline_supported: bool


class LanguagesResponse(BaseModel):
    languages: list[LanguageDetail]
    grouped: dict[str, list[LanguageDetail]]


class CapabilitiesResponse(BaseModel):
    active_asr_backend: str
    active_nmt_backend: str
    active_tts_backend: str
    mock_mode: bool
    languages: dict[str, dict[str, Any]]


# --- WebSocket Messages ---

class WSStartMessage(BaseModel):
    type: str = "start"
    source_lang: str = "ta"
    target_lang: str = "ml"
    audio_format: str = "pcm_s16le"
    sample_rate: int = 16000
    channels: int = 1


class WSStopMessage(BaseModel):
    type: str = "stop"


class WSPartialTranscriptMessage(BaseModel):
    type: str = "partial_transcript"
    text: str
    detected_lang: Optional[str] = None


class WSTranslationMessage(BaseModel):
    type: str = "translation"
    transcript: str
    translation: str
    source_lang: str
    target_lang: str
    detected_lang: Optional[str] = None
    entities_locked: list[LockedEntity] = Field(default_factory=list)
    stage_latencies_ms: dict[str, float] = Field(default_factory=dict)
    latency_ms: float
    offline: bool = False
    warning: Optional[str] = None


class WSAudioChunkMessage(BaseModel):
    type: str = "audio_chunk"
    sequence: int
    sample_rate: int = 16000
    encoding: str = "pcm_s16le"
    data: str  # Base64 encoded PCM16 bytes


# --- Pedagogy & PDF Models ---

class FlashcardGenerationRequest(BaseModel):
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="ml")
    category: Optional[str] = None
    title: Optional[str] = Field(default="Bilingual Flashcards")
    cols: int = Field(default=2, ge=1, le=4)
    rows: int = Field(default=4, ge=1, le=6)


class NumeracyWorksheetRequest(BaseModel):
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="ml")
    grade: int = Field(default=1, ge=1, le=3)
    include_student_name: bool = True


class LiteracyWorksheetRequest(BaseModel):
    source_lang: str = Field(default="ta")
    target_lang: str = Field(default="ml")
    grade: int = Field(default=1, ge=1, le=3)
    category: Optional[str] = None


class PDFGenerationResponse(BaseModel):
    file_name: str
    download_url: str
    page_count: int = 1
    source_lang: str
    target_lang: str
    embedded_fonts_ok: bool = True
    message: str = "PDF generated successfully"


# --- Cache Models ---

class PhraseSchema(BaseModel):
    id: str
    category: str
    source_language: str
    target_language: str
    source_text: str
    target_text: str
    pronunciation: Optional[str] = ""
    verified: bool = False
    translation_status: str = "NEEDS_REVIEW"


class CacheStatsResponse(BaseModel):
    total_phrases: int
    verified_phrases: int
    unverified_phrases: int
    categories: list[str]
    languages_covered: list[str]
    cached_audio_count: int


# --- Health & Observability Models ---

class HealthResponse(BaseModel):
    status: str = "ok"
    app_name: str = "TRANSLARA"
    version: str = "1.0.0"
    mock_mode: bool = True
    demo_mode: bool = True
    asr: SubsystemStatus = SubsystemStatus.READY
    nmt: SubsystemStatus = SubsystemStatus.READY
    tts: SubsystemStatus = SubsystemStatus.READY
    cache: SubsystemStatus = SubsystemStatus.READY
    pedagogy: SubsystemStatus = SubsystemStatus.READY


class MetricsResponse(BaseModel):
    total_requests: int
    successful_requests: int
    failed_requests: int
    average_latency_ms: float
    p95_latency_ms: float
    offline_fallback_count: int
    cache_hit_rate: float


class ConfigResponse(BaseModel):
    app_name: str = "TRANSLARA"
    app_env: str
    mock_mode: bool
    demo_mode: bool
    source_language: str
    default_target_language: str
    asr_backend: str
    nmt_backend: str
    tts_backend: str
    latency_target_ms: int
