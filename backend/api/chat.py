"""
TRANSLARA AI Chatbot API Router with MSSQL Persistent Sessions and Message Storage.
"""
from __future__ import annotations

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.auth.dependencies import get_optional_user
from backend.database.models import User
from backend.database.repositories.chat_and_pedagogy_repo import ChatRepository
from backend.database.session import get_db
from backend.services.chat_service import get_chat_service

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])


class ChatMessageRequest(BaseModel):
    message: str = Field(..., min_length=1)
    session_id: Optional[str] = None
    source_lang: str = "ta"
    target_lang: str = "ml"


class ChatSessionResponse(BaseModel):
    id: str
    title: str
    language: str
    created_at: str
    updated_at: str
    message_count: int = 0


@router.post("")
@router.post("/message")
async def send_chat_message(
    req: ChatMessageRequest,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """
    Send text or voice transcript message to TRANSLARA AI educational assistant.
    Persists user message and assistant response to MSSQL.
    """
    chat_repo = ChatRepository(db)

    # 1. Get or create session
    session_id = req.session_id or f"session_{uuid.uuid4().hex[:12]}"
    session = chat_repo.get_or_create_session(
        session_id=session_id,
        user_id=user.id if user else None,
        title=req.message[:50] + ("..." if len(req.message) > 50 else ""),
        language=req.source_lang,
    )

    # 2. Save user message to MSSQL
    chat_repo.save_message(
        session_id=session.id,
        role="user",
        message=req.message,
        language=req.source_lang,
        model_used="user_input",
    )

    # 3. Generate response using AI engine
    chat_service = get_chat_service()
    res = await chat_service.generate_response(
        user_text=req.message,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )

    # 4. Save assistant response to MSSQL
    chat_repo.save_message(
        session_id=session.id,
        role="assistant",
        message=res.translated_text or res.text,
        language=req.target_lang,
        model_used="TRANSLARA-Edu",
    )

    return {
        "id": res.id,
        "session_id": session.id,
        "sender": res.sender,
        "text": res.text,
        "translated_text": res.translated_text,
        "language": res.language,
        "target_language": res.target_language,
        "timestamp": res.timestamp,
    }


@router.get("/sessions")
async def list_chat_sessions(
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """List chat sessions from MSSQL."""
    chat_repo = ChatRepository(db)
    user_id = user.id if user else None
    sessions = chat_repo.list_sessions(user_id=user_id)
    return [
        {
            "id": s.id,
            "title": s.title,
            "language": s.language,
            "created_at": s.created_at.isoformat() if s.created_at else None,
            "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            "message_count": len(s.messages) if s.messages else 0,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}")
async def get_chat_session_details(
    session_id: str,
    db: Session = Depends(get_db),
    user: Optional[User] = Depends(get_optional_user),
):
    """Get all messages for a specific chat session."""
    chat_repo = ChatRepository(db)
    session = chat_repo.get_session_by_id(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = chat_repo.get_messages(session_id)
    return {
        "id": session.id,
        "title": session.title,
        "language": session.language,
        "created_at": session.created_at.isoformat() if session.created_at else None,
        "messages": [
            {
                "id": m.id,
                "role": m.role,
                "message": m.message,
                "language": m.language,
                "model_used": m.model_used,
                "created_at": m.created_at.isoformat() if m.created_at else None,
            }
            for m in messages
        ],
    }


@router.get("/history")
async def get_chat_history():
    """Retrieve in-memory / active session conversation history."""
    chat_service = get_chat_service()
    history = chat_service.get_history()
    return [
        {
            "id": m.id,
            "sender": m.sender,
            "text": m.text,
            "translated_text": m.translated_text,
            "language": m.language,
            "target_language": m.target_language,
            "timestamp": m.timestamp,
        }
        for m in history
    ]


@router.delete("/history")
async def clear_chat_history():
    """Clear in-memory conversation history."""
    chat_service = get_chat_service()
    chat_service.clear_history()
    return {"status": "cleared"}


@router.delete("/sessions/{session_id}")
async def delete_chat_session(
    session_id: str,
    db: Session = Depends(get_db),
):
    """Delete a chat session and all its messages from MSSQL."""
    chat_repo = ChatRepository(db)
    deleted = chat_repo.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return {"status": "deleted", "session_id": session_id}
