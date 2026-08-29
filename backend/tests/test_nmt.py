"""
Unit tests for TRANSLARA Multilingual NMT Translation Layer.
"""
import pytest
from backend.exceptions import UnsupportedLanguagePairError
from backend.ml_engine.nmt import MockNMT, get_nmt_backend


@pytest.mark.asyncio
async def test_tamil_to_malayalam():
    """TEST 1: Tamil -> Malayalam."""
    nmt = MockNMT()
    res = await nmt.translate("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "ml")
    assert res.text == "നമസ്കാരം, സുഖമാണോ?"
    assert res.src_lang == "ta"
    assert res.tgt_lang == "ml"
    assert res.confidence > 0.9


@pytest.mark.asyncio
async def test_malayalam_to_tamil():
    """TEST 2: Malayalam -> Tamil."""
    nmt = MockNMT()
    res = await nmt.translate("നമസ്കാരം, സുഖമാണോ?", "ml", "ta")
    assert res.text == "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
    assert res.src_lang == "ml"
    assert res.tgt_lang == "ta"


@pytest.mark.asyncio
async def test_tamil_to_hindi():
    """TEST 3: Tamil -> Hindi."""
    nmt = MockNMT()
    res = await nmt.translate("வணக்கம்", "ta", "hi")
    assert res.text == "नमस्ते"
    assert res.src_lang == "ta"
    assert res.tgt_lang == "hi"


@pytest.mark.asyncio
async def test_hindi_to_tamil():
    """TEST 4: Hindi -> Tamil."""
    nmt = MockNMT()
    res = await nmt.translate("नमस्ते", "hi", "ta")
    assert res.text == "வணக்கம்"
    assert res.src_lang == "hi"
    assert res.tgt_lang == "ta"


@pytest.mark.asyncio
async def test_telugu_to_tamil():
    """TEST 5: Telugu -> Tamil."""
    nmt = MockNMT()
    res = await nmt.translate("నమస్కారం, మీరు ఎలా ఉన్నారు?", "te", "ta")
    assert res.text == "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?"
    assert res.src_lang == "te"
    assert res.tgt_lang == "ta"


@pytest.mark.asyncio
async def test_kannada_to_malayalam():
    """TEST 6: Kannada -> Malayalam."""
    nmt = MockNMT()
    res = await nmt.translate("ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?", "kn", "ml")
    assert res.text == "നമസ്കാരം, സുഖമാണോ?"
    assert res.src_lang == "kn"
    assert res.tgt_lang == "ml"


@pytest.mark.asyncio
async def test_unsupported_language_pair_error():
    """Verify UnsupportedLanguagePairError is raised for invalid pairs."""
    nmt = MockNMT()
    with pytest.raises(UnsupportedLanguagePairError):
        await nmt.translate("Hello", "ta", "xyz_invalid")

    with pytest.raises(UnsupportedLanguagePairError):
        await nmt.translate("Hello", "ta", "ta")  # Same source and target
