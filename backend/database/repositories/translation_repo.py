"""
Translation and History Repository for TRANSLARA MSSQL Database.
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
        input_type: str = "text",
        model_used: str = "TRANSLARA-NMT-v1",
        model_version: str = "1.0",
        latency_ms: float = 0.0,
        offline_used: bool = False,
        validation_passed: bool = True,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> TranslationHistory:
        """Create and commit a translation history record in MSSQL."""
        record = TranslationHistory(
            user_id=user_id,
            session_id=session_id,
            source_language=source_language,
            target_language=target_language,
            source_text=source_text,
            translated_text=translated_text,
            input_type=input_type,
            model_used=model_used,
            model_version=model_version,
            latency_ms=latency_ms,
            offline_used=offline_used,
            validation_passed=validation_passed,
        )
        self.db.add(record)
        self.db.commit()
        self.db.refresh(record)
        return record

    def get_history_by_user(
        self,
        user_id: Optional[int] = None,
        is_admin: bool = False,
        limit: int = 50,
        offset: int = 0,
    ) -> List[TranslationHistory]:
        """Fetch translation history filtered by user_id or all if admin."""
        query = self.db.query(TranslationHistory)
        if not is_admin:
            if user_id is not None:
                query = query.filter(TranslationHistory.user_id == user_id)
            else:
                # Guest sessions: return recent without user_id
                query = query.filter(TranslationHistory.user_id == None)
        return query.order_by(TranslationHistory.created_at.desc()).offset(offset).limit(limit).all()

    def get_history_by_id(self, history_id: int) -> Optional[TranslationHistory]:
        """Fetch a specific history entry by primary key ID."""
        return self.db.query(TranslationHistory).filter(TranslationHistory.id == history_id).first()

    def delete_history_by_id(
        self,
        history_id: int,
        user_id: Optional[int] = None,
        is_admin: bool = False,
    ) -> bool:
        """Delete a translation history entry if authorized."""
        query = self.db.query(TranslationHistory).filter(TranslationHistory.id == history_id)
        if not is_admin and user_id is not None:
            query = query.filter(TranslationHistory.user_id == user_id)

        record = query.first()
        if not record:
            return False

        self.db.delete(record)
        self.db.commit()
        return True

    def find_cached_translation(
        self, source_text: str, source_language: str, target_language: str
    ) -> Optional[Translation]:
        """Find pre-verified translation from translations table."""
        return (
            self.db.query(Translation)
            .filter(
                Translation.source_language == source_language,
                Translation.target_language == target_language,
                Translation.source_text == source_text.strip(),
            )
            .first()
        )
