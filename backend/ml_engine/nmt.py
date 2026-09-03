"""
Neural Machine Translation (NMT) Layer for TRANSLARA.

Supports generic SOURCE -> TARGET translation across South and North Indian languages:
- Tamil (ta)
- Telugu (te)
- Kannada (kn)
- Malayalam (ml)
- Hindi (hi)
- Santhali (sat), Ho (hoc), Mundari (unr)

Backends:
1. AI4Bharat IndicTrans2
2. Bhashini ULCA
3. MockNMT (High-fidelity bidirectional demo pairs)
"""
from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass
from typing import Optional

from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from backend.config import settings
from backend.exceptions import UnsupportedLanguagePairError
from backend.ml_engine.languages import get_language, is_pair_supported


@dataclass
class Translation:
    text: str
    src_lang: str
    tgt_lang: str
    latency_ms: float
    backend: str
    confidence: float = 1.0
    low_confidence: bool = False
    warning: Optional[str] = None


class BaseNMT:
    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> Translation:
        raise NotImplementedError


class IndicTrans2Local(BaseNMT):
    """Self-hosted AI4Bharat IndicTrans2 model."""

    def __init__(self):
        try:
            import torch
            from transformers import AutoModelForSeq2SeqLM, AutoTokenizer

            logger.info(f"Loading IndicTrans2 model: {settings.indictrans2_model_id}")
            self._tokenizer = AutoTokenizer.from_pretrained(settings.indictrans2_model_id, trust_remote_code=True)
            self._model = AutoModelForSeq2SeqLM.from_pretrained(settings.indictrans2_model_id, trust_remote_code=True)
            self._model.eval()
            self._torch = torch
            self._ready = True
        except Exception as e:
            logger.warning(f"IndicTrans2 local model unavailable ({e}); will fall back to MockNMT")
            self._ready = False

    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> Translation:
        if not is_pair_supported(src_lang, tgt_lang):
            raise UnsupportedLanguagePairError(src_lang, tgt_lang)

        if not getattr(self, "_ready", False):
            mock = MockNMT()
            return await mock.translate(text, src_lang, tgt_lang)

        start = time.monotonic()
        src_cfg = get_language(src_lang)
        tgt_cfg = get_language(tgt_lang)
        if not src_cfg or not tgt_cfg:
            raise UnsupportedLanguagePairError(src_lang, tgt_lang)

        src_tag = src_cfg.indictrans2_tag
        tgt_tag = tgt_cfg.indictrans2_tag

        loop = asyncio.get_running_loop()

        def _run():
            tagged_input = f"{src_tag} {tgt_tag} {text}"
            inputs = self._tokenizer(tagged_input, return_tensors="pt", truncation=True, max_length=256)
            with self._torch.no_grad():
                out_ids = self._model.generate(
                    **inputs,
                    max_length=256,
                    num_beams=2,
                    early_stopping=True,
                )
            return self._tokenizer.decode(out_ids[0], skip_special_tokens=True)

        translated = await loop.run_in_executor(None, _run)
        latency_ms = (time.monotonic() - start) * 1000

        return Translation(
            text=translated,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            latency_ms=latency_ms,
            backend="indictrans2_local",
            confidence=0.91,
        )


# BhashiniULCA removed — 100% Local AI Model Architecture active


class MockNMT(BaseNMT):
    """
    Multilingual bidirectional mock NMT engine for TRANSLARA supporting South & North Indian pairs.
    """

    _KNOWN_PAIRS = {
        # --- English <-> Tamil ---
        ("Hello", "en", "ta"): "வணக்கம்",
        ("hello", "en", "ta"): "வணக்கம்",
        ("வணக்கம்", "ta", "en"): "Hello",
        ("Hello, how are you?", "en", "ta"): "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        ("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "en"): "Hello, how are you?",
        ("Open your book.", "en", "ta"): "புத்தகத்தைத் திறக்கவும்.",
        ("Open your book", "en", "ta"): "புத்தகத்தைத் திறக்கவும்",
        ("புத்தகத்தைத் திறக்கவும்.", "ta", "en"): "Open your book.",
        ("புத்தகத்தைத் திறக்கவும்", "ta", "en"): "Open your book",
        ("Thank you", "en", "ta"): "நன்றி",
        ("Thank you.", "en", "ta"): "நன்றி.",
        ("நன்றி", "ta", "en"): "Thank you",
        ("Good morning", "en", "ta"): "காலை வணக்கம்",
        ("காலை வணக்கம்", "ta", "en"): "Good morning",
        ("Good morning students, please sit down.", "en", "ta"): "காலை வணக்கம் மாணவர்களே, உட்காருங்கள்.",
        ("Today we will learn numbers from 1 to 10.", "en", "ta"): "இன்று நாம் 1 முதல் 10 வரை எண்களைக் கற்றுக்கொள்வோம்.",

        # --- English <-> Malayalam ---
        ("Hello", "en", "ml"): "നമസ്കാരം",
        ("hello", "en", "ml"): "നമസ്കാരം",
        ("നമസ്കാരം", "ml", "en"): "Hello",
        ("Hello, how are you?", "en", "ml"): "നമസ്കാരം, സുഖമാണോ?",
        ("നമസ്കാരം, സുഖമാണോ?", "ml", "en"): "Hello, how are you?",
        ("Open your book.", "en", "ml"): "പുസ്തകം തുറക്കൂ.",
        ("Open your book", "en", "ml"): "പുസ്തകം തുറക്കൂ",
        ("പുസ്തകം തുറക്കൂ.", "ml", "en"): "Open your book.",
        ("പുസ്തകം തുറക്കൂ", "ml", "en"): "Open your book",
        ("Thank you", "en", "ml"): "നന്ദി",
        ("Thank you.", "en", "ml"): "നന്ദി.",
        ("നന്ദി", "ml", "en"): "Thank you",
        ("Good morning", "en", "ml"): "സുപ്രഭാതം",
        ("സുപ്രഭാതം", "ml", "en"): "Good morning",
        ("Good morning students, please sit down.", "en", "ml"): "സുപ്രഭാതം കുട്ടികളേ, ഇരിക്കൂ.",
        ("Today we will learn numbers from 1 to 10.", "en", "ml"): "ഇന്ന് നമുക്ക് 1 മുതൽ 10 വരെയുള്ള അക്കങ്ങൾ പഠിക്കാം.",

        # --- English <-> Telugu ---
        ("Hello", "en", "te"): "నమస్కారం",
        ("hello", "en", "te"): "నమస్కారం",
        ("నమస్కారం", "te", "en"): "Hello",
        ("Hello, how are you?", "en", "te"): "నమస్కారం, మీరు ఎలా ఉన్నారు?",
        ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "en"): "Hello, how are you?",
        ("Open your book.", "en", "te"): "పుస్తకం తెరవండి.",
        ("పుస్తకం తెరవండి.", "te", "en"): "Open your book.",
        ("Thank you", "en", "te"): "ధన్యవాదాలు",
        ("ధన్యవాదాలు", "te", "en"): "Thank you",
        ("Good morning", "en", "te"): "శుభోదయం",
        ("శుభోదయం", "te", "en"): "Good morning",

        # --- English <-> Kannada ---
        ("Hello", "en", "kn"): "ನಮಸ್ಕಾರ",
        ("hello", "en", "kn"): "ನಮಸ್ಕಾರ",
        ("ನಮಸ್ಕಾರ", "kn", "en"): "Hello",
        ("Hello, how are you?", "en", "kn"): "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        ("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", "kn", "en"): "Hello, how are you?",
        ("Open your book.", "en", "kn"): "ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.",
        ("ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.", "kn", "en"): "Open your book.",
        ("Thank you", "en", "kn"): "ಧನ್ಯವಾದಗಳು",
        ("ಧನ್ಯವಾದಗಳು", "kn", "en"): "Thank you",
        ("Good morning", "en", "kn"): "ಶುಭೋದಯ",
        ("ಶುಭೋದಯ", "kn", "en"): "Good morning",

        # --- English <-> Hindi ---
        ("Hello", "en", "hi"): "नमस्ते",
        ("hello", "en", "hi"): "नमस्ते",
        ("नमस्ते", "hi", "en"): "Hello",
        ("Hello, how are you?", "en", "hi"): "नमस्ते, आप कैसे हैं?",
        ("नमस्ते, आप कैसे हैं?", "hi", "en"): "Hello, how are you?",
        ("Open your book.", "en", "hi"): "किताब खोलो।",
        ("Open your book", "en", "hi"): "किताब खोलो",
        ("किताब खोलो।", "hi", "en"): "Open your book.",
        ("किताब खोलो", "hi", "en"): "Open your book",
        ("Thank you", "en", "hi"): "धन्यवाद",
        ("Thank you.", "en", "hi"): "धन्यवाद.",
        ("धन्यवाद", "hi", "en"): "Thank you",
        ("Good morning", "en", "hi"): "सुप्रभात",
        ("सुप्रभात", "hi", "en"): "Good morning",
        ("Children open your book.", "en", "hi"): "बच्चों किताब खोलो।",
        ("बच्चों किताब खोलो।", "hi", "en"): "Children open your book.",

        # --- English <-> Santhali / Ho / Mundari ---
        ("Hello", "en", "sat"): "ᱡᱚᱦᱟᱨ",
        ("hello", "en", "sat"): "ᱡᱚᱦᱟᱨ",
        ("ᱡᱚᱦᱟᱨ", "sat", "en"): "Hello",
        ("Open your book.", "en", "sat"): "ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾",
        ("Hello", "en", "hoc"): "जोहार",
        ("जोहार", "hoc", "en"): "Hello",
        ("Hello", "en", "unr"): "जोहार",
        ("जोहार", "unr", "en"): "Hello",

        # --- Tamil -> Malayalam ---
        ("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "ml"): "നമസ്കാരം, സുഖമാണോ?",
        ("வணக்கம்", "ta", "ml"): "നമസ്കാരം",
        ("புத்தகத்தைத் திறக்கவும்.", "ta", "ml"): "പുസ്തകം തുറക്കൂ.",
        ("புத்தகத்தைத் திறக்கவும்", "ta", "ml"): "പുസ്തകം തുറക്കൂ",
        ("நன்றி", "ta", "ml"): "നന്ദി",
        ("காலை வணக்கம்", "ta", "ml"): "സുപ്രഭാതം",

        # --- Malayalam -> Tamil ---
        ("നമസ്കാരം, സുഖമാണോ?", "ml", "ta"): "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        ("നമസ്കാരം", "ml", "ta"): "வணக்கம்",
        ("പുസ്തകം തുറക്കൂ.", "ml", "ta"): "புத்தகத்தைத் திறக்கவும்.",
        ("നന്ദി", "ml", "ta"): "நன்றி",
        ("സുപ്രഭാതം", "ml", "ta"): "காலை வணக்கம்",

        # --- Tamil -> Hindi ---
        ("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "hi"): "नमस्ते, आप कैसे हैं?",
        ("வணக்கம்", "ta", "hi"): "नमस्ते",
        ("புத்தகத்தைத் திறக்கவும்.", "ta", "hi"): "किताब खोलो।",
        ("நன்றி", "ta", "hi"): "धन्यवाद",

        # --- Hindi -> Tamil ---
        ("नमस्ते, आप कैसे हैं?", "hi", "ta"): "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        ("नमस्ते", "hi", "ta"): "வணக்கம்",
        ("बच्चों किताब खोलो।", "hi", "ta"): "மாணவர்களே புத்தகத்தைத் திறக்கவும்.",
        ("धन्यवाद", "hi", "ta"): "நன்றி",

        # --- Telugu -> Tamil ---
        ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "ta"): "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        ("నమస్కారం", "te", "ta"): "வணக்கம்",
        ("పుస్తకం తెరవండి.", "te", "ta"): "புத்தகத்தைத் திறக்கவும்.",
        ("ధన్యవాదాలు", "te", "ta"): "நன்றி",

        # --- Telugu -> Hindi ---
        ("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "hi"): "नमस्ते, आप कैसे हैं?",
        ("పుస్తకం తెరవండి.", "te", "hi"): "किताब खोलो।",

        # --- Kannada -> Malayalam ---
        ("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", "kn", "ml"): "നമസ്കാരം, സുഖമാണോ?",
        ("ನಮಸ್ಕಾರ", "kn", "ml"): "നമസ്കാരം",
        ("ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.", "kn", "ml"): "പുസ്തകം തുറക്കൂ.",
        ("ಧನ್ಯವಾದಗಳು", "kn", "ml"): "നന്ദി",

        # --- Kannada -> Tamil ---
        ("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", "kn", "ta"): "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        ("ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.", "kn", "ta"): "புத்தகத்தைத் திறக்கவும்.",

        # --- Hindi -> Santhali / Ho / Mundari ---
        ("बच्चों किताब खोलो।", "hi", "sat"): "ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾",
        ("अपनी किताब खोलो", "hi", "sat"): "ᱟᱢᱟᱜ ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ",
        ("नमस्ते", "hi", "sat"): "ᱡᱚᱦᱟᱨ",
        ("बच्चों किताब खोलो।", "hi", "hoc"): "होनको पोथी निहके पे.",
        ("बच्चों किताब खोलो।", "hi", "unr"): "होनको पुथी ओलोल पे.",

        # --- Tamil -> Santhali ---
        ("புத்தகத்தைத் திறக்கவும்.", "ta", "sat"): "ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾",
        ("வணக்கம்", "ta", "sat"): "ᱡᱚᱦᱟᱨ",
    }

    async def translate(self, text: str, src_lang: str, tgt_lang: str) -> Translation:
        start = time.monotonic()
        await asyncio.sleep(0.16)

        # Validate pair
        if not is_pair_supported(src_lang, tgt_lang):
            raise UnsupportedLanguagePairError(src_lang, tgt_lang)

        # Check exact translation table
        key = (text.strip(), src_lang, tgt_lang)
        if key in self._KNOWN_PAIRS:
            return Translation(
                text=self._KNOWN_PAIRS[key],
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                latency_ms=(time.monotonic() - start) * 1000,
                backend="mock_nmt",
                confidence=0.98,
            )

        # Dynamic Entity Mask Handling for South and North Indian Languages + English
        if "⟦ENT" in text:
            translated = text
            if tgt_lang == "en":
                # English entity template: "⟦ENT0⟧ has ⟦ENT1⟧ books."
                translated = f"⟦ENT0⟧ has ⟦ENT1⟧ books."
            elif tgt_lang == "ml":
                # Malayalam entity template: "⟦ENT0⟧-ന്റെ കൈയിൽ ⟦ENT1⟧ പുസ്തകങ്ങളുണ്ട്."
                translated = (
                    text.replace("அருணிடம்", "⟦ENT0⟧")
                    .replace("கிட்ட", "കൈയിൽ")
                    .replace("புத்தகங்கள் உள்ளன.", "പുസ്തകങ്ങളുണ്ട്.")
                    .replace("புத்தகங்கள் உள்ளன", "പുസ്തകങ്ങളുണ്ട്")
                    .replace("के पास", "കൈയിൽ")
                    .replace("किताबें हैं।", "പുസ്തകങ്ങളുണ്ട്.")
                    .replace("దగ్గర", "കൈയിൽ")
                    .replace("పుస్తకాలు ఉన్నాయి.", "പുസ്തകങ്ങളുണ്ട്.")
                    .replace("ಬಳಿ", "കൈയിൽ")
                    .replace("ಪುಸ್ತಕಗಳಿವೆ.", "പുസ്തകങ്ങളുണ്ട്.")
                )
                if "⟦ENT0⟧" in translated and "കൈയിൽ" not in translated and "പുസ്തകങ്ങളുണ്ട്" not in translated:
                    translated = f"⟦ENT0⟧-ന്റെ കൈയിൽ ⟦ENT1⟧ പുസ്തകങ്ങളുണ്ട്."

            elif tgt_lang == "ta":
                # Tamil entity template: "⟦ENT0⟧-இடம் ⟦ENT1⟧ புத்தகங்கள் உள்ளன."
                translated = (
                    text.replace("കൈയിൽ", "இடம்")
                    .replace("പുസ്തകങ്ങളുണ്ട്.", "புத்தகங்கள் உள்ளன.")
                    .replace("के पास", "இடம்")
                    .replace("किताबें हैं।", "புத்தகங்கள் உள்ளன.")
                    .replace("దగ్గర", "இடம்")
                    .replace("పుస్తకాలు ఉన్నాయి.", "புத்தகங்கள் உள்ளன.")
                    .replace("ಬಳಿ", "இடம்")
                    .replace("ಪುಸ್ತಕಗಳಿವೆ.", "புத்தகங்கள் உள்ளன.")
                )
                if "⟦ENT0⟧" in translated and "புத்தகங்கள்" not in translated:
                    translated = f"⟦ENT0⟧-இடம் ⟦ENT1⟧ புத்தகங்கள் உள்ளன."

            elif tgt_lang == "te":
                # Telugu entity template: "⟦ENT0⟧ దగ్గర ⟦ENT1⟧ పుస్తకాలు ఉన్నాయి."
                translated = f"⟦ENT0⟧ దగ్గర ⟦ENT1⟧ పుస్తకాలు ఉన్నాయి."

            elif tgt_lang == "kn":
                # Kannada entity template: "⟦ENT0⟧ ಬಳಿ ⟦ENT1⟧ ಪುಸ್ತಕಗಳಿವೆ."
                translated = f"⟦ENT0⟧ ಬಳಿ ⟦ENT1⟧ ಪುಸ್ತಕಗಳಿವೆ."

            elif tgt_lang == "hi":
                # Hindi entity template: "⟦ENT0⟧ के पास ⟦ENT1⟧ किताबें हैं।"
                translated = f"⟦ENT0⟧ के पास ⟦ENT1⟧ किताबें हैं."

            elif tgt_lang == "sat":
                # Santhali entity template: "⟦ENT0⟧ ᱴᱷᱮᱱ ⟦ENT1⟧ ᱜᱚᱴᱟᱝ ᱯᱩᱛᱷᱤ ᱢᱮᱱᱟᱜᱼᱟ᱾"
                translated = f"⟦ENT0⟧ ᱴᱷᱮᱱ ⟦ENT1⟧ ᱜᱚᱴᱟᱝ ᱯᱩᱛᱷᱤ ᱢᱮᱱᱟᱜᱼᱟ᱾"

            return Translation(
                text=translated,
                src_lang=src_lang,
                tgt_lang=tgt_lang,
                latency_ms=(time.monotonic() - start) * 1000,
                backend="mock_nmt",
                confidence=0.96,
            )

        # Fallback with low confidence tag
        tgt_cfg = get_language(tgt_lang)
        lang_name = tgt_cfg.name if tgt_cfg else tgt_lang
        translated = f"[{lang_name}: {text}]"

        return Translation(
            text=translated,
            src_lang=src_lang,
            tgt_lang=tgt_lang,
            latency_ms=(time.monotonic() - start) * 1000,
            backend="mock_nmt",
            confidence=0.65,
            low_confidence=True,
            warning="DEMO_UNVERIFIED_PAIR",
        )


_nmt_singleton: Optional[BaseNMT] = None


def get_nmt_backend() -> BaseNMT:
    global _nmt_singleton
    if _nmt_singleton is None:
        if settings.mock_mode:
            logger.info("Using Multilingual MockNMT (MOCK_MODE=True)")
            _nmt_singleton = MockNMT()
        elif settings.nmt_backend in ("indictrans2", "indictrans2_local", "local_nmt"):
            _nmt_singleton = IndicTrans2Local()
        else:
            _nmt_singleton = MockNMT()
    return _nmt_singleton
