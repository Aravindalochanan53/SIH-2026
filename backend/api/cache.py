"""
Offline Phrase Cache API Router for TRANSLARA.
"""
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.cache.database import get_db
from backend.cache.models import Phrase
from backend.cache.offline_store import get_offline_store
from backend.cache.seed_cache import seed_all
from backend.schemas import CacheStatsResponse, PhraseSchema

router = APIRouter(prefix="/api/cache", tags=["Offline Cache"])


@router.get("/phrases", response_model=list[PhraseSchema])
async def list_phrases(
    category: Optional[str] = None,
    source_lang: Optional[str] = None,
    target_lang: Optional[str] = None,
    verified_only: bool = False,
    db: Session = Depends(get_db),
):
    """Query offline SQLite phrases."""
    q = db.query(Phrase)
    if category:
        q = q.filter(Phrase.category == category)
    if source_lang:
        q = q.filter(Phrase.source_language == source_lang)
    if target_lang:
        q = q.filter(Phrase.target_language == target_lang)
    if verified_only:
        q = q.filter(Phrase.verified.is_(True))

    phrases = q.limit(200).all()
    return [
        PhraseSchema(
            id=p.id,
            category=p.category,
            source_language=p.source_language,
            target_language=p.target_language,
            source_text=p.source_text,
            target_text=p.target_text,
            pronunciation=p.pronunciation or "",
            verified=p.verified,
            translation_status=p.translation_status,
        )
        for p in phrases
    ]


@router.get("/stats", response_model=CacheStatsResponse)
async def get_cache_stats(db: Session = Depends(get_db)):
    """Return offline phrase count and verification stats."""
    total = db.query(Phrase).count()
    verified = db.query(Phrase).filter(Phrase.verified.is_(True)).count()
    categories = [c[0] for c in db.query(Phrase.category).distinct().all()]

    return CacheStatsResponse(
        total_phrases=total,
        verified_phrases=verified,
        unverified_phrases=total - verified,
        categories=categories,
        languages_covered=["ta", "te", "kn", "ml", "hi", "sat", "hoc", "unr"],
        cached_audio_count=48,
    )


@router.post("/seed")
async def trigger_seed():
    """Seed default phrases into SQLite database."""
    p_cnt, e_cnt = seed_all()
    store = get_offline_store()
    store.reload()
    return {
        "status": "seeded",
        "phrases_seeded": p_cnt,
        "entities_seeded": e_cnt,
    }


@router.post("/verify/{phrase_id}")
async def verify_phrase(phrase_id: str, db: Session = Depends(get_db)):
    """Mark phrase verified by educator."""
    phrase = db.query(Phrase).filter(Phrase.id == phrase_id).first()
    if not phrase:
        raise HTTPException(status_code=404, detail="Phrase not found")

    phrase.verified = True
    phrase.translation_status = "VERIFIED"
    db.commit()

    store = get_offline_store()
    store.reload()

    return {"status": "verified", "phrase_id": phrase.id}
