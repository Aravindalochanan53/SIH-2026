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
                text="Hello! I am TRANSLARA AI, your multilingual classroom assistant. How can I help you with translations, lesson plans, or primary worksheets today?",
                language="en",
                translated_text="வணக்கம்! நான் TRANSLARA AI. வகுப்பறை மொழிபெயர்ப்பு, சொற்களஞ்சியம் மற்றும் கற்பித்தலில் உங்களுக்கு எப்படி உதவ முடியும்?",
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
        """Generate specialized vernacular educational response using TRANSLARA AI."""
        engine = get_translation_engine()
        src_cfg = get_language(source_lang)
        tgt_cfg = get_language(target_lang)
        src_name = src_cfg.name if src_cfg else source_lang
        tgt_name = tgt_cfg.name if tgt_cfg else target_lang

        user_lower = user_text.lower().strip()

        # Check if user requested a direct translation
        if user_lower.startswith("translate") or "மொழிபெயர்க்க" in user_text or "വിവർത്തനം" in user_text:
            cleaned_input = user_text
            for prefix in ["translate", "translate this:", "translate:"]:
                if user_lower.startswith(prefix):
                    cleaned_input = user_text[len(prefix):].strip()
                    break

            trans_res = await engine.translate(cleaned_input, source_lang, target_lang)
            ans_text = f"Translation ({tgt_name}):\n{trans_res.text}"
            trans_text = trans_res.text

        elif "explain" in user_lower or "number" in user_lower or "counting" in user_lower:
            ans_text = (
                f"Foundational Numeracy Guide (Grade 1):\n"
                f"1 - One (🍎 One apple)\n"
                f"2 - Two (🍎🍎 Two apples)\n"
                f"3 - Three (⭐ Three stars)\n"
                f"4 - Four (🚗 Four cars)\n"
                f"5 - Five (🖐️ Five fingers on a hand)"
            )
            trans_res = await engine.translate("Count the objects from 1 to 5.", source_lang, target_lang)
            trans_text = f"{tgt_name}: {trans_res.text}"

        elif "worksheet" in user_lower or "activity" in user_lower:
            ans_text = (
                f"Grade 1 Bilingual {src_name} & {tgt_name} Worksheet is ready! You can generate and download the printable PDF in the Worksheet Studio."
            )
            trans_res = await engine.translate("Grade 1 Bilingual Worksheet is ready.", source_lang, target_lang)
            trans_text = trans_res.text

        elif "simplify" in user_lower or "grade 1" in user_lower:
            ans_text = (
                f"Simplified for Grade 1: Use short visual sentences, repeating phrases, and picture cards."
            )
            trans_res = await engine.translate("Look at the picture. Read this word.", source_lang, target_lang)
            trans_text = f"{tgt_name}: {trans_res.text}"

        else:
            trans_res = await engine.translate(user_text, source_lang, target_lang)
            ans_text = f"Here is the educational explanation for '{user_text}':"
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
