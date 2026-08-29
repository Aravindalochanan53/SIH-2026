"""
Centralized application configuration for TRANSLARA.

Controls pan-Indian multilingual routing, model selection, timeouts, VAD parameters,
mock/demo toggles, database connection, and CORS settings without modifying source code.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Literal
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment & Branding
    app_name: str = "TRANSLARA"
    app_env: str = "development"
    log_level: str = "INFO"
    host: str = "0.0.0.0"
    port: int = 8000

    # Development & SIH Operational Modes
    mock_mode: bool = False
    demo_mode: bool = False

    # Pan-Indian Languages: Default to South Indian Pair (Tamil -> Malayalam)
    source_language: str = "ta"
    default_target_language: str = "ml"

    # ASR Configuration (Multilingual Faster-Whisper, IndicConformer, MMS, Mock)
    asr_backend: Literal["faster_whisper", "indic_conformer", "mms", "mock"] = "faster_whisper"
    whisper_model_size: str = "small"
    whisper_device: str = "cpu"
    whisper_compute_type: str = "int8"
    indic_conformer_endpoint: str = "http://localhost:8500/infer"
    mms_model_id: str = "facebook/mms-1b-all"

    # NMT Configuration (Generic Source -> Target, IndicTrans2 / Bhashini)
    nmt_backend: Literal["indictrans2", "indictrans2_local", "bhashini_ulca", "mock"] = "indictrans2"
    indictrans2_model_id: str = "ai4bharat/indictrans2-indic-indic-dist-320M"
    bhashini_user_id: str = ""
    bhashini_ulca_api_key: str = ""
    bhashini_inference_api_key: str = ""
    bhashini_pipeline_id: str = "64392f96daac500b55c543cd"
    bhashini_api_url: str = "https://dhruva-api.bhashini.gov.in/services/inference/pipeline"

    # TTS Configuration (Multilingual Indic-TTS / VITS / Mock)
    tts_backend: Literal["indic_tts", "vits_local", "indic_tts_api", "mock"] = "indic_tts"
    indic_tts_endpoint: str = "https://api.indictts.example.org/synthesize"
    tts_chunk_ms: int = 200

    # VAD Configuration
    vad_aggressiveness: int = 2
    vad_frame_ms: int = 30
    vad_tail_silence_ms: int = 260
    vad_min_utterance_ms: int = 250
    vad_max_utterance_ms: int = 12000

    # Latency Budget & Timeouts (ms)
    asr_timeout_ms: int = 1200
    nmt_timeout_ms: int = 1400
    tts_timeout_ms: int = 1000
    total_latency_target_ms: int = 3000

    # Database & Storage
    database_url: str = f"sqlite:///{BASE_DIR / 'data' / 'translara.db'}"
    cache_enabled: bool = True
    offline_fallback_enabled: bool = True
    store_audio: bool = False

    # Security & Networking
    cors_origins: str = "http://localhost:5173,http://localhost:3000,chrome-extension://*"
    websocket_max_message_size: int = 5242880  # 5MB

    # Storage Paths
    model_cache_dir: str = str(BASE_DIR / "models")
    audio_cache_dir: str = str(BASE_DIR / "backend" / "assets" / "translara_audio")
    pdf_output_dir: str = str(BASE_DIR / "backend" / "assets" / "translara_pdfs")
    fonts_dir: str = str(BASE_DIR / "backend" / "assets" / "fonts")
    data_dir: str = str(BASE_DIR / "backend" / "data")

    # Font Overrides for South and North Indian Scripts
    tamil_font_path: str = ""
    telugu_font_path: str = ""
    kannada_font_path: str = ""
    malayalam_font_path: str = ""
    hindi_font_path: str = ""
    santhali_font_path: str = ""
    ho_font_path: str = ""
    mundari_font_path: str = ""

    def get_cors_origins_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


settings = Settings()

# Ensure directories exist
for p in [settings.audio_cache_dir, settings.pdf_output_dir, settings.fonts_dir, str(BASE_DIR / "data")]:
    Path(p).mkdir(parents=True, exist_ok=True)
