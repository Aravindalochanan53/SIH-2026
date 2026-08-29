"""
Seed Database with Pan-Indian Educational Phrases and Gazetteers for TRANSLARA.
"""
from __future__ import annotations

import json
from pathlib import Path
from loguru import logger
from sqlalchemy.orm import Session

from backend.cache.database import SessionLocal, init_db
from backend.cache.models import EntityRecord, Phrase

# Seed phrase pairs across South & North Indian Languages
SEED_PHRASES = [
    # --- Greetings & Courtesies (English -> Tamil / Malayalam / Hindi) ---
    {
        "id": "greetings_en_ta_01",
        "category": "greetings",
        "source_language": "en",
        "target_language": "ta",
        "source_text": "Hello, how are you?",
        "target_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        "pronunciation": "Hello, how are you? -> Vanakkam, neengal eppadi irukkeergal?",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "greetings_en_ta_02",
        "category": "greetings",
        "source_language": "en",
        "target_language": "ta",
        "source_text": "Good morning",
        "target_text": "காலை வணக்கம்",
        "pronunciation": "Good morning -> Kaalai vanakkam",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "courtesy_en_ta_01",
        "category": "courtesy",
        "source_language": "en",
        "target_language": "ta",
        "source_text": "Thank you",
        "target_text": "நன்றி",
        "pronunciation": "Thank you -> Nandri",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_en_ta_01",
        "category": "classroom_instructions",
        "source_language": "en",
        "target_language": "ta",
        "source_text": "Open your book.",
        "target_text": "புத்தகத்தைத் திறக்கவும்.",
        "pronunciation": "Open your book -> Puthagathai thirakkavum",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "greetings_en_ml_01",
        "category": "greetings",
        "source_language": "en",
        "target_language": "ml",
        "source_text": "Hello, how are you?",
        "target_text": "നമസ്കാരം, സുഖമാണോ?",
        "pronunciation": "Hello, how are you? -> Namaskaram, sukhamaano?",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_en_ml_01",
        "category": "classroom_instructions",
        "source_language": "en",
        "target_language": "ml",
        "source_text": "Open your book.",
        "target_text": "പുസ്തകം തുറക്കൂ.",
        "pronunciation": "Open your book -> Pusthakam thurakkoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    # --- Greetings & Courtesies (Tamil -> Malayalam) ---
    {
        "id": "greetings_ta_ml_01",
        "category": "greetings",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        "target_text": "നമസ്കാരം, സുഖമാണോ?",
        "pronunciation": "Vanakkam, neengal eppadi irukkeergal? -> Namaskaram, sukhamaano?",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "greetings_ta_ml_02",
        "category": "greetings",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "காலை வணக்கம்",
        "target_text": "സുപ്രഭാതം",
        "pronunciation": "Kaalai vanakkam -> Suprabhaatham",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "courtesy_ta_ml_01",
        "category": "courtesy",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "நன்றி",
        "target_text": "നന്ദി",
        "pronunciation": "Nandri -> Nandi",
        "verified": True,
        "translation_status": "VERIFIED",
    },

    # --- Classroom Instructions (Tamil -> Malayalam) ---
    {
        "id": "classroom_ta_ml_01",
        "category": "classroom_instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "புத்தகத்தைத் திறக்கவும்.",
        "target_text": "പുസ്തകം തുറക്കൂ.",
        "pronunciation": "Puthagathai thirakkavum -> Pusthakam thurakkoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_ta_ml_02",
        "category": "classroom_instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "இங்கே வாருங்கள்",
        "target_text": "ഇവിടെ വരൂ",
        "pronunciation": "Inge vaarungal -> Ivide varoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_ta_ml_03",
        "category": "classroom_instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "உட்காருங்கள்",
        "target_text": "ഇരിക്കൂ",
        "pronunciation": "Utkaarungal -> Irikkoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_ta_ml_04",
        "category": "classroom_instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "எழுந்து நில்லுங்கள்",
        "target_text": "എഴുന്നേൽക്കൂ",
        "pronunciation": "Ezhundhu nillungal -> Ezhunnelkoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },

    # --- Tamil -> Hindi ---
    {
        "id": "greetings_ta_hi_01",
        "category": "greetings",
        "source_language": "ta",
        "target_language": "hi",
        "source_text": "வணக்கம்",
        "target_text": "नमस्ते",
        "pronunciation": "Vanakkam -> Namaste",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_ta_hi_01",
        "category": "classroom_instructions",
        "source_language": "ta",
        "target_language": "hi",
        "source_text": "புத்தகத்தைத் திறக்கவும்.",
        "target_text": "किताब खोलो।",
        "pronunciation": "Puthagathai thirakkavum -> Kitaab kholo",
        "verified": True,
        "translation_status": "VERIFIED",
    },

    # --- Telugu -> Tamil ---
    {
        "id": "greetings_te_ta_01",
        "category": "greetings",
        "source_language": "te",
        "target_language": "ta",
        "source_text": "నమస్కారం, మీరు ఎలా ఉన్నారు?",
        "target_text": "வணக்கம், நீங்கள் எப்படி இருக்கிறீர்கள்?",
        "pronunciation": "Namaskaram, meeru ela unnaru? -> Vanakkam, neengal eppadi irukkeergal?",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_te_ta_01",
        "category": "classroom_instructions",
        "source_language": "te",
        "target_language": "ta",
        "source_text": "పుస్తకం తెరవండి.",
        "target_text": "புத்தகத்தைத் திறக்கவும்.",
        "pronunciation": "Pusthakam teravandi -> Puthagathai thirakkavum",
        "verified": True,
        "translation_status": "VERIFIED",
    },

    # --- Kannada -> Malayalam ---
    {
        "id": "greetings_kn_ml_01",
        "category": "greetings",
        "source_language": "kn",
        "target_language": "ml",
        "source_text": "ನಮಸ್ಕಾರ, ನೀವು ಹೇಗಿದ್ದೀರಿ?",
        "target_text": "നമസ്കാരം, സുഖമാണോ?",
        "pronunciation": "Namaskara, neevu hegiddiri? -> Namaskaram, sukhamaano?",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_kn_ml_01",
        "category": "classroom_instructions",
        "source_language": "kn",
        "target_language": "ml",
        "source_text": "ಪುಸ್ತಕವನ್ನು ತೆರೆಯಿರಿ.",
        "target_text": "പുസ്തകം തുറക്കൂ.",
        "pronunciation": "Pusthakavannu tereyiri -> Pusthakam thurakkoo",
        "verified": True,
        "translation_status": "VERIFIED",
    },

    # --- Hindi -> Santhali / Tribal ---
    {
        "id": "classroom_hi_sat_01",
        "category": "classroom_instructions",
        "source_language": "hi",
        "target_language": "sat",
        "source_text": "बच्चों किताब खोलो।",
        "target_text": "ᱜᱤᱫᱽᱨᱟᱹ ᱠᱚ ᱯᱩᱛᱷᱤ ᱡᱷᱤᱡᱽ ᱢᱮ᱾",
        "pronunciation": "Bachho kitaab kholo -> Gidra ko puthi jhij me",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_hi_sat_02",
        "category": "classroom_instructions",
        "source_language": "hi",
        "target_language": "sat",
        "source_text": "यहाँ आओ",
        "target_text": "ᱱᱚᱸᱰᱮ ᱦᱤᱡᱩᱜ ᱢᱮ",
        "pronunciation": "Yahan aao -> Nonde hijug me",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "greetings_hi_sat_01",
        "category": "greetings",
        "source_language": "hi",
        "target_language": "sat",
        "source_text": "नमस्ते",
        "target_text": "ᱡᱚᱦᱟᱨ",
        "pronunciation": "Namaste -> Johar",
        "verified": True,
        "translation_status": "VERIFIED",
    },
    {
        "id": "classroom_hi_hoc_01",
        "category": "classroom_instructions",
        "source_language": "hi",
        "target_language": "hoc",
        "source_text": "बच्चों किताब खोलो।",
        "target_text": "होनको पोथी निहके पे।",
        "pronunciation": "Bachho kitaab kholo -> Honko pothi nihke pe",
        "verified": False,
        "translation_status": "NEEDS_REVIEW",
    },
    {
        "id": "classroom_hi_unr_01",
        "category": "classroom_instructions",
        "source_language": "hi",
        "target_language": "unr",
        "source_text": "बच्चों किताब खोलो।",
        "target_text": "होनको पुथी ओलोल पे।",
        "pronunciation": "Bachho kitaab kholo -> Honko puthi olol pe",
        "verified": False,
        "translation_status": "NEEDS_REVIEW",
    },
]

# Pan-Indian Gazetteers
SEED_ENTITIES = [
    # South Indian Student Names
    {"name": "Arun", "kind": "PERSON", "phonetic_hint": "uh-roon", "language": "ta"},
    {"name": "Priya", "kind": "PERSON", "phonetic_hint": "pree-yah", "language": "ta"},
    {"name": "Murugan", "kind": "PERSON", "phonetic_hint": "moo-roo-gun", "language": "ta"},
    {"name": "Lakshmi", "kind": "PERSON", "phonetic_hint": "luhk-shmee", "language": "all"},
    {"name": "Venkat", "kind": "PERSON", "phonetic_hint": "ven-kuht", "language": "te"},
    {"name": "Suresh", "kind": "PERSON", "phonetic_hint": "soo-raysh", "language": "all"},
    {"name": "Manju", "kind": "PERSON", "phonetic_hint": "mun-joo", "language": "kn"},
    {"name": "Manoj", "kind": "PERSON", "phonetic_hint": "muh-nohj", "language": "ml"},
    {"name": "அருண்", "kind": "PERSON", "phonetic_hint": "Arun", "language": "ta"},
    {"name": "பிரியா", "kind": "PERSON", "phonetic_hint": "Priya", "language": "ta"},
    {"name": "முருகன்", "kind": "PERSON", "phonetic_hint": "Murugan", "language": "ta"},
    {"name": "లక్ష్మి", "kind": "PERSON", "phonetic_hint": "Lakshmi", "language": "te"},
    {"name": "ಅರುಣ್", "kind": "PERSON", "phonetic_hint": "Arun", "language": "kn"},
    {"name": "അരുൺ", "kind": "PERSON", "phonetic_hint": "Arun", "language": "ml"},

    # North & Tribal Names
    {"name": "Sona Murmu", "kind": "PERSON", "phonetic_hint": "so-nah moor-moo", "language": "sat"},
    {"name": "Birsa Munda", "kind": "PERSON", "phonetic_hint": "beer-sah moon-dah", "language": "unr"},
    {"name": "Budhni Hembrom", "kind": "PERSON", "phonetic_hint": "boodh-nee hem-brom", "language": "sat"},

    # South Indian Locations & Cities
    {"name": "Chennai", "kind": "LOCATION", "phonetic_hint": "chen-nai", "language": "ta"},
    {"name": "Madurai", "kind": "LOCATION", "phonetic_hint": "mah-doo-rye", "language": "ta"},
    {"name": "Hyderabad", "kind": "LOCATION", "phonetic_hint": "hy-der-ah-bahd", "language": "te"},
    {"name": "Visakhapatnam", "kind": "LOCATION", "phonetic_hint": "vi-sah-khah-put-num", "language": "te"},
    {"name": "Bengaluru", "kind": "LOCATION", "phonetic_hint": "beng-ah-loo-roo", "language": "kn"},
    {"name": "Mysuru", "kind": "LOCATION", "phonetic_hint": "my-soo-roo", "language": "kn"},
    {"name": "Kochi", "kind": "LOCATION", "phonetic_hint": "koh-chee", "language": "ml"},
    {"name": "Thiruvananthapuram", "kind": "LOCATION", "phonetic_hint": "thir-oo-vun-un-thuh-poo-rum", "language": "ml"},
    {"name": "சென்னை", "kind": "LOCATION", "phonetic_hint": "Chennai", "language": "ta"},
    {"name": "மதுரை", "kind": "LOCATION", "phonetic_hint": "Madurai", "language": "ta"},
    {"name": "హైదరాబాద్", "kind": "LOCATION", "phonetic_hint": "Hyderabad", "language": "te"},
    {"name": "ಬೆಂಗಳೂರು", "kind": "LOCATION", "phonetic_hint": "Bengaluru", "language": "kn"},
    {"name": "തിരുവനന്തപുരം", "kind": "LOCATION", "phonetic_hint": "Thiruvananthapuram", "language": "ml"},

    # Eastern / Tribal Villages
    {"name": "Netarhat", "kind": "VILLAGE", "phonetic_hint": "nay-tur-haht", "language": "hi"},
    {"name": "Bishunpur", "kind": "VILLAGE", "phonetic_hint": "bish-oon-poor", "language": "hi"},
    {"name": "Ranchi", "kind": "LOCATION", "phonetic_hint": "rahn-chee", "language": "hi"},
]


def seed_all() -> tuple[int, int]:
    """Seed phrases and entities into SQLite database."""
    init_db()
    db: Session = SessionLocal()
    phrases_count = 0
    entities_count = 0

    try:
        # Seed Phrases
        for item in SEED_PHRASES:
            phrase = Phrase(
                id=item["id"],
                category=item["category"],
                source_language=item["source_language"],
                target_language=item["target_language"],
                source_text=item["source_text"],
                target_text=item["target_text"],
                pronunciation=item.get("pronunciation", ""),
                verified=item.get("verified", False),
                translation_status=item.get("translation_status", "NEEDS_REVIEW"),
            )
            db.merge(phrase)
            phrases_count += 1

        # Seed Entities
        for e in SEED_ENTITIES:
            existing = db.query(EntityRecord).filter(EntityRecord.name == e["name"]).first()
            if not existing:
                ent = EntityRecord(
                    name=e["name"],
                    kind=e["kind"],
                    language=e.get("language", "all"),
                    phonetic_hint=e.get("phonetic_hint"),
                )
                db.add(ent)
                entities_count += 1

        db.commit()
        logger.info(
            f"TRANSLARA Database Seed: {phrases_count} phrases merged, {entities_count} entities added"
        )
    except Exception as err:
        db.rollback()
        logger.error(f"Error seeding database: {err}")
    finally:
        db.close()

    return phrases_count, entities_count
