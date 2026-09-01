"""
Chat Sessions, Messages, and Pedagogy Repository for TRANSLARA MSSQL Database.
"""
from __future__ import annotations

from typing import List, Optional
from sqlalchemy.orm import Session
from backend.database.models import ChatMessage, ChatSession, Flashcard, Worksheet


class ChatRepository:
    def __init__(self, db: Session):
        self.db = db

    def get_or_create_session(
        self,
        session_id: Optional[str] = None,
        user_id: Optional[int] = None,
        title: str = "AI Teaching Assistant Session",
        language: str = "ta",
    ) -> ChatSession:
        if session_id:
            session = self.db.query(ChatSession).filter(ChatSession.id == session_id).first()
            if session:
                return session

        session = ChatSession(
            id=session_id,
            user_id=user_id,
            title=title,
            language=language,
        )
        self.db.add(session)
        self.db.commit()
        self.db.refresh(session)
        return session

    def list_sessions(self, user_id: Optional[int] = None, limit: int = 50) -> List[ChatSession]:
        query = self.db.query(ChatSession)
        if user_id is not None:
            query = query.filter(ChatSession.user_id == user_id)
        return query.order_by(ChatSession.updated_at.desc()).limit(limit).all()

    def get_session_by_id(self, session_id: str) -> Optional[ChatSession]:
        return self.db.query(ChatSession).filter(ChatSession.id == session_id).first()

    def save_message(
        self,
        session_id: str,
        role: str,
        message: str,
        language: str = "ta",
        model_used: str = "TRANSLARA-Edu",
        message_id: Optional[str] = None,
    ) -> ChatMessage:
        msg = ChatMessage(
            id=message_id,
            session_id=session_id,
            role=role,
            message=message,
            language=language,
            model_used=model_used,
        )
        self.db.add(msg)
        self.db.commit()
        self.db.refresh(msg)
        return msg

    def get_messages(self, session_id: str) -> List[ChatMessage]:
        return (
            self.db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )

    def delete_session(self, session_id: str) -> bool:
        session = self.get_session_by_id(session_id)
        if not session:
            return False
        self.db.delete(session)
        self.db.commit()
        return True


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
        file_path: str,
        user_id: Optional[int] = None,
    ) -> Worksheet:
        ws = Worksheet(
            id=worksheet_id,
            user_id=user_id,
            title=title,
            grade=str(grade),
            subject=subject,
            language=source_language,
            target_language=target_language,
            file_path=file_path,
        )
        self.db.add(ws)
        self.db.commit()
        self.db.refresh(ws)
        return ws

    def list_worksheets(self, user_id: Optional[int] = None, limit: int = 50) -> List[Worksheet]:
        query = self.db.query(Worksheet)
        if user_id is not None:
            query = query.filter(Worksheet.user_id == user_id)
        return query.order_by(Worksheet.created_at.desc()).limit(limit).all()

    def save_flashcard(
        self,
        flashcard_id: str,
        deck_name: str,
        word: str,
        translation: str,
        source_language: str,
        target_language: str,
        category: str = "General",
        file_path: Optional[str] = None,
        user_id: Optional[int] = None,
    ) -> Flashcard:
        card = Flashcard(
            id=flashcard_id,
            user_id=user_id,
            deck_name=deck_name,
            word=word,
            translation=translation,
            source_language=source_language,
            target_language=target_language,
            category=category,
            file_path=file_path,
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
