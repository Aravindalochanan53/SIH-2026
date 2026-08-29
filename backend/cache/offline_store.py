"""
Offline Phrase Lookup Store for TRANSLARA.

Provides sub-millisecond in-memory phrase matching across South and North Indian languages.
"""
from __future__ import annotations

import re
import unicodedata
from typing import Optional
from loguru import logger
from sqlalchemy.orm import Session

from backend.cache.database import SessionLocal
from backend.cache.models import Phrase


def normalize_text(text: str) -> str:
    """Normalize text for invariant lookup without stripping Indian unicode scripts."""
    text = unicodedata.normalize("NFKC", text.strip())
    # Remove punctuation
    text = re.sub(r"[।॥.,!?;:'\"()\[\]{}\-—\s]+", " ", text)
    return text.strip().lower()


class OfflineStore:
    def __init__(self):
        # Index: (normalized_source_text, source_lang, target_lang) -> target_text
        self._index: dict[tuple[str, str, str], str] = {}
        self._phrases_by_id: dict[str, Phrase] = {}
        self._load_memory_index()

    def _load_memory_index(self) -> None:
        db: Session = SessionLocal()
        try:
            phrases = db.query(Phrase).all()
            for p in phrases:
                self._phrases_by_id[p.id] = p
                src_key = (normalize_text(p.source_text), p.source_language.lower(), p.target_language.lower())
                self._index[src_key] = p.target_text

                # If symmetric bidirectional mapping
                rev_key = (normalize_text(p.target_text), p.target_language.lower(), p.source_language.lower())
                if rev_key not in self._index:
                    self._index[rev_key] = p.source_text

            logger.info(f"TRANSLARA OfflineStore: Indexed {len(self._index)} phrase mappings into memory")
        except Exception as e:
            logger.warning(f"Error loading offline memory index: {e}")
        finally:
            db.close()

    def reload(self) -> None:
        self._index.clear()
        self._phrases_by_id.clear()
        self._load_memory_index()

    def lookup_translation(self, text: str, src_lang: str, tgt_lang: str) -> Optional[str]:
        """Sub-millisecond translation lookup in offline cache."""
        norm = normalize_text(text)
        key = (norm, src_lang.lower().strip(), tgt_lang.lower().strip())
        res = self._index.get(key)
        if res:
            return res

        # Check DB directly if newly inserted
        db: Session = SessionLocal()
        try:
            match = (
                db.query(Phrase)
                .filter(
                    Phrase.source_language == src_lang.lower().strip(),
                    Phrase.target_language == tgt_lang.lower().strip(),
                    Phrase.source_text == text.strip(),
                )
                .first()
            )
            if match:
                self._index[key] = match.target_text
                return match.target_text
        finally:
            db.close()

        return None

    def find_phrase(self, text: str, src_lang: Optional[str] = None) -> Optional[Phrase]:
        """Find phrase record."""
        norm = normalize_text(text)
        for (n_src, s_lang, t_lang), tgt_txt in self._index.items():
            if n_src == norm:
                if src_lang is None or s_lang == src_lang.lower():
                    # return from memory
                    for p in self._phrases_by_id.values():
                        if normalize_text(p.source_text) == norm:
                            return p
        return None

    def get_stats(self) -> dict:
        db: Session = SessionLocal()
        try:
            total = db.query(Phrase).count()
            verified = db.query(Phrase).filter(Phrase.verified.is_(True)).count()
            unverified = total - verified
            categories = [c[0] for c in db.query(Phrase.category).distinct().all()]
            return {
                "total_phrases": total,
                "verified_phrases": verified,
                "unverified_phrases": unverified,
                "categories": categories,
            }
        finally:
            db.close()


_offline_store_singleton: Optional[OfflineStore] = None


def get_offline_store() -> OfflineStore:
    global _offline_store_singleton
    if _offline_store_singleton is None:
        _offline_store_singleton = OfflineStore()
    return _offline_store_singleton
