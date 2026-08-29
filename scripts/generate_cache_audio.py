"""
Pre-render and Cache Audio for Verified Phrases.
Run: python scripts/generate_cache_audio.py
"""
import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.cache.database import SessionLocal, init_db
from backend.cache.models import Phrase
from backend.cache.audio_cache import get_audio_cache_manager
from backend.ml_engine.tts import get_tts_backend


async def pre_render_all():
    print("Pre-rendering audio for verified phrases in TRANSLARA cache...")
    init_db()
    db = SessionLocal()
    audio_mgr = get_audio_cache_manager()
    tts = get_tts_backend()

    phrases = db.query(Phrase).filter(Phrase.verified.is_(True)).all()
    count = 0

    for p in phrases:
        if p.target_text and "NEEDS_REVIEW" not in p.translation_status:
            chunks = []
            async for chunk in tts.synthesize_stream(p.target_text, p.target_language):
                chunks.append(chunk)
            full_pcm = b"".join(chunks)
            if full_pcm:
                audio_mgr.save_audio(p.id, p.target_language, full_pcm)
                count += 1

    db.close()
    print(f"Pre-rendered and cached {count} audio files.")


if __name__ == "__main__":
    asyncio.run(pre_render_all())
