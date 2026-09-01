"""
Centralized application configuration for TRANSLARA.

Controls pan-Indian multilingual routing, model selection, timeouts, VAD parameters,
mock/demo toggles, MSSQL database connection, JWT authentication, and CORS settings.
"""
from __future__ import annotations

import os
import urllib.parse
from pathlib import Path
from typing import Literal, Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=[str(BACKEND_DIR / ".env"), str(BASE_DIR / ".env")],
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # General Environment & Branding
    app_name: str = Field(default="TRANSLARA", alias="APP_NAME")
    app_env: str = Field(default="development", alias="APP_ENV")
    debug: bool = Field(default=True, alias="DEBUG")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    host: str = Field(default="127.0.0.1", alias="HOST")
    port: int = Field(default=8000, alias="PORT")

    # Development & SIH Operational Modes
    mock_mode: bool = Field(default=False, alias="MOCK_MODE")
    demo_mode: bool = Field(default=False, alias="DEMO_MODE")

    # Microsoft SQL Server (MSSQL) Database Configuration
    db_server: str = Field(default="localhost", alias="DB_SERVER")
    db_port: int = Field(default=1433, alias="DB_PORT")
    db_name: str = Field(default="TRANSLARA", alias="DB_NAME")
    db_user: Optional[str] = Field(default=None, alias="DB_USER")
    db_password: Optional[str] = Field(default=None, alias="DB_PASSWORD")
    db_driver: str = Field(default="ODBC Driver 18 for SQL Server", alias="DB_DRIVER")
    db_trust_server_certificate: bool = Field(default=True, alias="DB_TRUST_SERVER_CERTIFICATE")
    database_url: Optional[str] = Field(default=None, alias="DATABASE_URL")

    # JWT Authentication & Security
    jwt_secret_key: str = Field(
        default="translara_production_secret_key_change_in_env_2026_sih",
        alias="JWT_SECRET_KEY",
    )
    jwt_algorithm: str = Field(default="HS256", alias="JWT_ALGORITHM")
    jwt_access_token_expire_minutes: int = Field(
        default=60 * 24 * 7, alias="JWT_ACCESS_TOKEN_EXPIRE_MINUTES"
    )  # 7 days

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

    # Offline SQLite Cache & Local Fallback
    cache_enabled: bool = True
    offline_fallback_enabled: bool = True
    offline_db_url: str = f"sqlite:///{BASE_DIR / 'data' / 'translara.db'}"
    store_audio: bool = False

    # Security & Networking
    cors_origins: str = "http://localhost:5173,http://localhost:3000,http://127.0.0.1:5173,chrome-extension://*"
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

    def get_database_url(self) -> str:
        """
        Construct or return the SQLAlchemy connection URL.
        Priority:
        1. Explicit DATABASE_URL if configured.
        2. MSSQL connection string built from DB_* parameters.
        3. Local fallback SQLite cache URL.
        """
        if self.database_url and self.database_url.strip():
            return self.database_url.strip()

        # If user provided DB_USER or DB_SERVER
        if self.db_user and self.db_password:
            driver_str = urllib.parse.quote_plus(self.db_driver)
            trust_cert = "yes" if self.db_trust_server_certificate else "no"
            user_enc = urllib.parse.quote_plus(self.db_user)
            pwd_enc = urllib.parse.quote_plus(self.db_password)
            return (
                f"mssql+pyodbc://{user_enc}:{pwd_enc}@{self.db_server}:{self.db_port}/{self.db_name}"
                f"?driver={driver_str}&TrustServerCertificate={trust_cert}"
            )
        elif self.db_server and self.db_server.lower() not in ("none", ""):
            # Trusted Windows Authentication (no user/password)
            driver_str = urllib.parse.quote_plus(self.db_driver)
            trust_cert = "yes" if self.db_trust_server_certificate else "no"
            return (
                f"mssql+pyodbc://@{self.db_server}:{self.db_port}/{self.db_name}"
                f"?driver={driver_str}&Trusted_Connection=yes&TrustServerCertificate={trust_cert}"
            )

        return self.offline_db_url


settings = Settings()

# Ensure directories exist
for p in [settings.audio_cache_dir, settings.pdf_output_dir, settings.fonts_dir, str(BASE_DIR / "data")]:
    Path(p).mkdir(parents=True, exist_ok=True)
