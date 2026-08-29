"""
TRANSLARA AI Chatbot API Router.
"""
from typing import Optional
from fastapi import APIRouter
from pydantic import BaseModel

from backend.services.chat_service import get_chat_service

router = APIRouter(prefix="/api/chat", tags=["AI Chatbot"])


class ChatMessageRequest(BaseModel):
    message: str
    source_lang: str = "ta"
    target_lang: str = "ml"


@router.post("/message")
async def send_chat_message(req: ChatMessageRequest):
    """Send text or voice transcript message to TRANSLARA AI educational assistant."""
    chat_service = get_chat_service()
    res = await chat_service.generate_response(
        user_text=req.message,
        source_lang=req.source_lang,
        target_lang=req.target_lang,
    )
    return {
        "id": res.id,
        "sender": res.sender,
        "text": res.text,
        "translated_text": res.translated_text,
        "language": res.language,
        "target_language": res.target_language,
        "timestamp": res.timestamp,
    }


@router.get("/history")
async def get_chat_history():
    """Retrieve conversation history."""
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
    """Clear conversation history."""
    chat_service = get_chat_service()
    chat_service.clear_history()
    return {"status": "cleared"}
