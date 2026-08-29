"""
High-Speed Deterministic Mock ASR Provider for testing and demo verification.
"""
from __future__ import annotations

import asyncio
import time
from typing import Optional

from backend.ai.asr.base import ASRResult, BaseASRProvider


class MockASRProvider(BaseASRProvider):
    _UTTERANCES_BY_LANG = {
        "en": [
            "Hello, how are you?",
            "Arun has 5 books.",
            "Open your book.",
            "Today we will learn numbers from 1 to 10.",
            "Good morning students, please sit down.",
        ],
        "ta": [
            "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
            "அருணிடம் 5 புத்தகங்கள் உள்ளன.",
            "புத்தகத்தைத் திறக்கவும்.",
            "இன்று நாம் 1 முதல் 10 வரை எண்களைக் கற்றுக்கொள்வோம்.",
            "காலை வணக்கம் மாணவர்களே, உட்காருங்கள்.",
        ],
        "te": [
            "నమస్కారం, మీరు ఎలా ఉన్నారు?",
            "అరుణ్ దగ్గర 5 పుస్తకాలు ఉన్నాయి.",
            "పుస్తకం తెరవండి.",
            "ఈ రోజు మనం 1 నుండి 10 వరకు సంఖ్యలను నేర్చుకుందాం.",
            "శుభోదయం పిల్లలు, కూర్చోండి.",
        ],
        "kn": [
            "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
            "ಅರುಣ್ ಬಳಿ 5 ಪುಸ್ತಕಗಳಿವೆ.",
            "ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.",
            "ಇಂದು ನಾವು 1 ರಿಂದ 10 ರವರೆಗೆ ಎಣಿಕೆಯನ್ನು ಕಲಿಯೋಣ.",
            "ಶುಭೋದಯ ಮಕ್ಕಳೇ, ಕುಳಿತುಕೊಳ್ಳಿ.",
        ],
        "ml": [
            "നമസ്കാരം, സുഖമാണോ?",
            "അരുണിന്റെ കൈയിൽ 5 പുസ്തകങ്ങളുണ്ട്.",
            "പുസ്തകം തുറക്കൂ.",
            "ഇന്ന് നമുക്ക് 1 മുതൽ 10 വരെയുള്ള അക്കങ്ങൾ പഠിക്കാം.",
            "സുപ്രഭാതം കുട്ടികളേ, ഇരിക്കൂ.",
        ],
        "hi": [
            "बच्चों किताब खोलो।",
            "Sona Murmu के पास 5 किताबें हैं।",
            "आज हम 1 से 10 तक गिनती सीखेंगे।",
            "सुप्रभात बच्चों, कृपया बैठिए।",
        ],
        "sat": [
            "ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾",
            "ᱡᱚᱦᱟᱨ",
        ],
        "hoc": [
            "होनको पोथी निहके पे।",
            "जोहार",
        ],
        "unr": [
            "होनको पुथी ओलोल पे।",
            "जोहार",
        ],
    }
    _counter = 0

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> ASRResult:
        start = time.monotonic()
        await asyncio.sleep(0.12)

        lang = hint_language or "en"
        if lang not in self._UTTERANCES_BY_LANG:
            lang = "en"

        options = self._UTTERANCES_BY_LANG.get(lang, ["Hello"])
        idx = MockASRProvider._counter % len(options)
        MockASRProvider._counter += 1
        text = options[idx]

        return ASRResult(
            text=text,
            language=lang,
            confidence=0.96,
            latency_ms=(time.monotonic() - start) * 1000,
            backend="mock_asr",
        )

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return "ta"
