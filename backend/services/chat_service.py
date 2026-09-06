"""
TRANSLARA AI — Educational Chatbot & Vernacular Pedagogy Assistant.
Powered by the central TRANSLARA AI Translation Engine.
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

from backend.ai.translation.registry import get_translation_engine
from backend.ml_engine.languages import get_language


@dataclass
class ChatMessage:
    id: str
    sender: str  # 'user' | 'assistant'
    text: str
    language: str
    translated_text: Optional[str] = None
    target_language: Optional[str] = None
    audio_available: bool = True
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class ChatService:
    _instance: Optional[ChatService] = None

    def __new__(cls) -> ChatService:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._history: list[ChatMessage] = []
            cls._instance._init_greeting()
        return cls._instance

    def _init_greeting(self) -> None:
        self._history = [
            ChatMessage(
                id="msg_welcome_01",
                sender="assistant",
                text="Hello! I am TRANSLARA AI, your multilingual translation and language assistant. Ask me to translate sentences, explain cross-lingual grammar nuances, or help with Indian language vocabulary.",
                language="en",
                translated_text="வணக்கம்! நான் TRANSLARA AI. பன்மொழி மொழிபெயர்ப்பு, சொற்களஞ்சியம் மற்றும் இலக்கண நுணுக்கங்களில் உங்களுக்கு எப்படி உதவ முடியும்?",
                target_language="ta",
            )
        ]

    def get_history(self) -> list[ChatMessage]:
        return list(self._history)

    def clear_history(self) -> None:
        self._history.clear()
        self._init_greeting()

    async def generate_response(
        self,
        user_text: str,
        source_lang: str = "en",
        target_lang: str = "ta",
    ) -> ChatMessage:
        """Generate specialized multilingual translation and grammar response using TRANSLARA AI."""
        engine = get_translation_engine()
        src_cfg = get_language(source_lang)
        tgt_cfg = get_language(target_lang)
        src_name = src_cfg.name if src_cfg else source_lang
        tgt_name = tgt_cfg.name if tgt_cfg else target_lang

        user_lower = user_text.lower().strip()

        # Check if user requested a direct translation or specific phrase
        cleaned_input = user_text
        for prefix in ["translate this:", "translate:", "translate", "meaning of:", "meaning of"]:
            if user_lower.startswith(prefix):
                cleaned_input = user_text[len(prefix):].strip()
                break

        trans_res = await engine.translate(cleaned_input, source_lang, target_lang)

        if "grammar" in user_lower or "rule" in user_lower or "tense" in user_lower:
            ans_text = (
                f"Grammar & Syntax Note ({src_name} → {tgt_name}):\n"
                f"• Source text: \"{cleaned_input}\"\n"
                f"• Translated text: \"{trans_res.text}\"\n"
                f"• Structure: {tgt_name} typically follows Subject-Object-Verb (SOV) order with postpositions."
            )
            trans_text = trans_res.text
        elif "idiom" in user_lower or "proverb" in user_lower or "phrase" in user_lower:
            ans_text = (
                f"Linguistic & Idiomatic Translation ({src_name} → {tgt_name}):\n"
                f"• Literal / Contextual translation: \"{trans_res.text}\""
            )
            trans_text = trans_res.text
        else:
            ans_text = f"Translation ({src_name} → {tgt_name}):\n{trans_res.text}"
            trans_text = trans_res.text

        # Record User Message
        u_msg = ChatMessage(
            id=f"msg_u_{int(time.time()*1000)}",
            sender="user",
            text=user_text,
            language=source_lang,
            target_language=target_lang,
        )
        self._history.append(u_msg)

        # Record Assistant Message
        a_msg = ChatMessage(
            id=f"msg_a_{int(time.time()*1000)}",
            sender="assistant",
            text=ans_text,
            language=source_lang,
            translated_text=trans_text,
            target_language=target_lang,
        )
        self._history.append(a_msg)

        return a_msg


def get_chat_service() -> ChatService:
    return ChatService()
