"""
Unit tests for TRANSLARA Multilingual Offline Cache.
"""
from backend.cache.database import SessionLocal, init_db
from backend.cache.models import Phrase
from backend.cache.offline_store import OfflineStore
from backend.cache.seed_cache import seed_all


def test_cache_seeding_and_lookup():
    """TEST 12: Offline cache works for South & North Indian pairs."""
    init_db()
    p_cnt, e_cnt = seed_all()
    assert p_cnt >= 0

    store = OfflineStore()
    trans = store.lookup_translation("வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?", "ta", "ml")
    assert trans is not None
    assert trans == "നമസ്കാരം, സുഖമാണോ?"


def test_offline_custom_phrase_lookup():
    db = SessionLocal()
    test_phrase = Phrase(
        id="test_offline_ta_hi_001",
        category="greetings",
        source_language="ta",
        target_language="hi",
        source_text="வணக்கம் தோழா",
        target_text="नमस्ते दोस्त",
        verified=True,
        translation_status="VERIFIED",
    )
    db.merge(test_phrase)
    db.commit()
    db.close()

    store = OfflineStore()
    store.reload()

    hi_trans = store.lookup_translation("வணக்கம் தோழா", "ta", "hi")
    assert hi_trans == "नमस्ते दोस्त"
