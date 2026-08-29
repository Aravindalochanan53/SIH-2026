"""
Unit tests for TRANSLARA AI Educational Chatbot.
"""
import pytest
from backend.services.chat_service import get_chat_service


@pytest.mark.asyncio
async def test_chat_educational_response():
    chat = get_chat_service()

    # Test numbers question
    reply = await chat.generate_response(
        user_text="Explain numbers 1 to 5 for Grade 1",
        source_lang="ta",
        target_lang="ml",
    )

    assert reply.sender == "assistant"
    assert "ஒன்று" in reply.text or "1" in reply.text
    assert reply.translated_text is not None
    assert "ഒന്ന്" in reply.translated_text or "1" in reply.translated_text


@pytest.mark.asyncio
async def test_chat_history_lifecycle():
    chat = get_chat_service()
    history = chat.get_history()
    assert len(history) > 0

    await chat.generate_response("Tell me about body parts in Tamil and Malayalam", "ta", "ml")
    new_history = chat.get_history()
    assert len(new_history) > len(history)
