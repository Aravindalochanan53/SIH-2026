"""
Classroom Phrase Repository for Offline Cache in TRANSLARA.
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import ClassroomPhrase


class PhraseRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_phrase(
        self, text: str, source_language: str, target_language: str
    ) -> Optional[ClassroomPhrase]:
        clean = text.strip()
        return (
            self.db.query(ClassroomPhrase)
            .filter(
                ClassroomPhrase.source_language == source_language,
                ClassroomPhrase.target_language == target_language,
                ClassroomPhrase.source_text == clean,
            )
            .first()
        )

    def get_phrases_by_category(
        self, category: str, source_language: str, target_language: str
    ) -> List[ClassroomPhrase]:
        return (
            self.db.query(ClassroomPhrase)
            .filter(
                ClassroomPhrase.category == category,
                ClassroomPhrase.source_language == source_language,
                ClassroomPhrase.target_language == target_language,
            )
            .all()
        )

    def add_phrase(
        self,
        category: str,
        source_language: str,
        target_language: str,
        source_text: str,
        target_text: str,
        audio_path: Optional[str] = None,
    ) -> ClassroomPhrase:
        phrase = ClassroomPhrase(
            category=category,
            source_language=source_language,
            target_language=target_language,
            source_text=source_text,
            target_text=target_text,
            audio_path=audio_path,
        )
        self.db.add(phrase)
        self.db.commit()
        self.db.refresh(phrase)
        return phrase
