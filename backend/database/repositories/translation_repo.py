"""
Translation and History Repository for TRANSLARA Database.
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import Translation, TranslationHistory


class TranslationRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_history(
        self,
        source_language: str,
        target_language: str,
        source_text: str,
        translated_text: str,
        mode: str = "text",
        latency_ms: float = 0.0,
        session_id: Optional[str] = None,
    ) -> TranslationHistory:
        record = TranslationHistory(
            session_id=session_id,
            source_language=source_language,
            target_language=target_language,
            source_text=source_text,
            translated_text=translated_text,
            mode=mode,
            latency_ms=latency_ms,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_recent_history(self, limit: int = 50) -> List[TranslationHistory]:
        return (
            self.db.query(TranslationHistory)
            .order_by(TranslationHistory.created_at.desc())
            .limit(limit)
            .all()
        )

    def find_cached_translation(
        self, source_text: str, source_language: str, target_language: str
    ) -> Optional[Translation]:
        return (
            self.db.query(Translation)
            .filter(
                Translation.source_language == source_language,
                Translation.target_language == target_language,
                Translation.source_text == source_text.strip(),
            )
            .first()
        )
