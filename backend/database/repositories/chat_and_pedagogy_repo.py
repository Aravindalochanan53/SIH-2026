"""
Chat History and Pedagogy Repository for TRANSLARA Database.
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import ChatHistory, Worksheet, Flashcard


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_message(
        self,
        message_id: str,
        sender: str,
        text: str,
        language: str,
        translated_text: Optional[str] = None,
        target_language: Optional[str] = None,
    ) -> ChatHistory:
        msg = ChatHistory(
            id=message_id,
            sender=sender,
            text=text,
            language=language,
            translated_text=translated_text,
            target_language=target_language,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_history(self, limit: int = 100) -> List[ChatHistory]:
        return self.db.query(ChatHistory).order_by(ChatHistory.timestamp.asc()).limit(limit).all()


class PedagogyRepository:
    def __init__(self, db: Session):
        self.db = db

    def save_worksheet(
        self,
        worksheet_id: str,
        title: str,
        grade: str,
        subject: str,
        source_language: str,
        target_language: str,
        pdf_path: str,
    ) -> Worksheet:
        ws = Worksheet(
            id=worksheet_id,
            title=title,
            grade=grade,
            subject=subject,
            source_language=source_language,
            target_language=target_language,
            pdf_path=pdf_path,
        )
        self.db.add(ws)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def list_worksheets(self, limit: int = 50) -> List[Worksheet]:
        return self.db.query(Worksheet).order_by(Worksheet.created_at.desc()).limit(limit).all()

    def save_flashcard(
        self,
        flashcard_id: str,
        deck_name: str,
        word: str,
        translation: str,
        source_language: str,
        target_language: str,
        category: str = "General",
        image_url: Optional[str] = None,
    ) -> Flashcard:
        card = Flashcard(
            id=flashcard_id,
            deck_name=deck_name,
            word=word,
            translation=translation,
            source_language=source_language,
            target_language=target_language,
            category=category,
            image_url=image_url,
        )
        self.db.add(card)
        self.db.commit()
        self.db.refresh(card)
        return card

    def get_flashcards(self, source_language: str, target_language: str) -> List[Flashcard]:
        return (
            self.db.query(Flashcard)
            .filter(
                Flashcard.source_language == source_language,
                Flashcard.target_language == target_language,
            )
            .all()
        )
