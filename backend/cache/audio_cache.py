"""
Audio Cache Management.
Stores and retrieves pre-synthesized PCM16 audio files for verified classroom phrases.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

from loguru import logger
from backend.config import settings
from backend.cache.database import SessionLocal
from backend.cache.models import AudioCache


class AudioCacheManager:
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path(settings.audio_cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def save_audio(self, phrase_id: str, language: str, pcm_bytes: bytes, sample_rate: int = 16000) -> str:
        """Save raw PCM bytes to disk and register in database."""
        filename = f"{phrase_id}_{language}.pcm"
        file_path = self.cache_dir / filename
        file_path.write_bytes(pcm_bytes)

        db = SessionLocal()
        try:
            record = (
                db.query(AudioCache)
                .filter(AudioCache.phrase_id == phrase_id, AudioCache.language == language)
                .first()
            )
            if not record:
                record = AudioCache(
                    phrase_id=phrase_id,
                    language=language,
                    audio_path=str(file_path),
                    sample_rate=sample_rate,
                )
                db.add(record)
            else:
                record.audio_path = str(file_path)
                record.sample_rate = sample_rate
            db.commit()
            return str(file_path)
        finally:
            db.close()

    def get_audio(self, phrase_id: str, language: str) -> Optional[bytes]:
        """Retrieve cached audio bytes if present."""
        db = SessionLocal()
        try:
            record = (
                db.query(AudioCache)
                .filter(AudioCache.phrase_id == phrase_id, AudioCache.language == language)
                .first()
            )
            if record and os.path.exists(record.audio_path):
                return Path(record.audio_path).read_bytes()
            return None
        finally:
            db.close()


_audio_cache_mgr: Optional[AudioCacheManager] = None


def get_audio_cache_manager() -> AudioCacheManager:
    global _audio_cache_mgr
    if _audio_cache_mgr is None:
        _audio_cache_mgr = AudioCacheManager()
    return _audio_cache_mgr
