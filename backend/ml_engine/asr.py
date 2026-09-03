"""
Automatic Speech Recognition (ASR) Layer for TRANSLARA.

Supports:
- Faster-Whisper (INT8 quantized, CPU/GPU) with multilingual support (Tamil, Telugu, Kannada, Malayalam, Hindi, etc.)
- Automatic language detection when hint_language="auto" or None
- IndicConformer hook for Indian languages
- Meta MMS hook for multilingual long-tail coverage
- MockASR for deterministic testing and SIH demo presentation across South & North Indian languages
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

import numpy as np
from loguru import logger

from backend.config import settings
from backend.ml_engine.languages import get_language

SAMPLE_RATE = 16000


@dataclass
class Transcript:
    text: str
    language: str          # Detected or declared source language code (e.g. "ta", "te", "ml", "hi")
    confidence: float      # Normalized 0.0 - 1.0
    latency_ms: float
    backend: str


class BaseASR:
    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> Transcript:
        raise NotImplementedError

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        """Detect language of spoken audio."""
        raise NotImplementedError


class FasterWhisperASR(BaseASR):
    """
    Multilingual Faster-Whisper backend with CTranslate2 and INT8 quantization.
    Supports Tamil, Telugu, Kannada, Malayalam, Hindi, and auto language identification.
    """

    def __init__(self):
        try:
            from faster_whisper import WhisperModel
            logger.info(
                f"Loading Multilingual Faster-Whisper model={settings.whisper_model_size} "
                f"device={settings.whisper_device} compute={settings.whisper_compute_type}"
            )
            self._model = WhisperModel(
                settings.whisper_model_size,
                device=settings.whisper_device,
                compute_type=settings.whisper_compute_type,
            )
            self._ready = True
        except Exception as e:
            logger.warning(f"Faster-Whisper not available ({e}); will fall back to MockASR")
            self._ready = False

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> Transcript:
        if not getattr(self, "_ready", False):
            mock = MockASR()
            return await mock.transcribe(pcm16_bytes, hint_language)

        start = time.monotonic()
        audio_f32 = _pcm16_to_float32(pcm16_bytes)

        # Handle 'auto' or unspecified language
        lang_arg = None if (hint_language in (None, "auto", "")) else hint_language

        loop = asyncio.get_running_loop()
        segments, info = await loop.run_in_executor(
            None,
            lambda: self._model.transcribe(
                audio_f32,
                language=lang_arg,
                vad_filter=False,
                beam_size=1,
                condition_on_previous_text=False,
            ),
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        latency_ms = (time.monotonic() - start) * 1000
        detected = info.language or (hint_language or "ta")

        return Transcript(
            text=text,
            language=detected,
            confidence=float(getattr(info, "language_probability", 0.0) or 0.88),
            latency_ms=latency_ms,
            backend="faster_whisper",
        )

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        t = await self.transcribe(pcm16_bytes, hint_language="auto")
        return t.language


class IndicConformerASR(BaseASR):
    """Local IndicConformer / Faster-Whisper ASR engine running 100% locally."""

    def __init__(self):
        self._local_fw = FasterWhisperASR()

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> Transcript:
        return await self._local_fw.transcribe(pcm16_bytes, hint_language=hint_language)

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return await self._local_fw.detect_language(pcm16_bytes)


class MMSASR(BaseASR):
    """Meta MMS fallback for multilingual Indian speech."""

    def __init__(self):
        try:
            from transformers import AutoProcessor, Wav2Vec2ForCTC
            logger.info(f"Loading MMS model {settings.mms_model_id}")
            self._processor = AutoProcessor.from_pretrained(settings.mms_model_id)
            self._model = Wav2Vec2ForCTC.from_pretrained(settings.mms_model_id)
            self._ready = True
        except Exception as e:
            logger.warning(f"Meta MMS not loaded ({e}); degrading gracefully")
            self._ready = False

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> Transcript:
        if not getattr(self, "_ready", False):
            mock = MockASR()
            return await mock.transcribe(pcm16_bytes, hint_language)

        import torch
        start = time.monotonic()
        audio_f32 = _pcm16_to_float32(pcm16_bytes)
        loop = asyncio.get_running_loop()
        lang_code = hint_language or "ta"

        def _run():
            if lang_code and lang_code != "auto":
                try:
                    self._processor.tokenizer.set_target_lang(lang_code)
                    self._model.load_adapter(lang_code)
                except Exception:
                    pass
            inputs = self._processor(audio_f32, sampling_rate=SAMPLE_RATE, return_tensors="pt")
            with torch.no_grad():
                logits = self._model(**inputs).logits
            ids = torch.argmax(logits, dim=-1)
            return self._processor.batch_decode(ids)[0]

        text = await loop.run_in_executor(None, _run)
        return Transcript(
            text=text,
            language=lang_code,
            confidence=0.78,
            latency_ms=(time.monotonic() - start) * 1000,
            backend="mms",
        )

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return "ta"


class MockASR(BaseASR):
    """
    High-speed deterministic mock ASR for TRANSLARA supporting South & North Indian languages.
    """

    # Realistic demo utterances per language
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

    async def transcribe(self, pcm16_bytes: bytes, hint_language: Optional[str] = None) -> Transcript:
        start = time.monotonic()
        await asyncio.sleep(0.14)  # Realistic 140ms latency simulation

        lang = hint_language if (hint_language and hint_language != "auto") else "ta"
        pool = self._UTTERANCES_BY_LANG.get(lang, self._UTTERANCES_BY_LANG["ta"])

        idx = MockASR._counter % len(pool)
        MockASR._counter += 1
        text = pool[idx]

        return Transcript(
            text=text,
            language=lang,
            confidence=0.96,
            latency_ms=(time.monotonic() - start) * 1000,
            backend="mock_asr",
        )

    async def detect_language(self, pcm16_bytes: bytes) -> str:
        return "ta"


def _pcm16_to_float32(pcm16_bytes: bytes) -> np.ndarray:
    audio_i16 = np.frombuffer(pcm16_bytes, dtype=np.int16)
    return (audio_i16.astype(np.float32)) / 32768.0


_asr_singleton: Optional[BaseASR] = None


def get_asr_backend() -> BaseASR:
    global _asr_singleton
    if _asr_singleton is None:
        if settings.mock_mode:
            logger.info("Using Multilingual MockASR (MOCK_MODE=True)")
            _asr_singleton = MockASR()
        elif settings.asr_backend == "faster_whisper":
            _asr_singleton = FasterWhisperASR()
        elif settings.asr_backend == "indic_conformer":
            _asr_singleton = IndicConformerASR()
        elif settings.asr_backend == "mms":
            _asr_singleton = MMSASR()
        else:
            _asr_singleton = MockASR()
    return _asr_singleton
