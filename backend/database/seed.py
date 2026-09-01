"""
Database Seeding Script for TRANSLARA MSSQL Database.
Populates standard pan-Indian languages and classroom vocabulary safely without deleting existing records.
"""
from __future__ import annotations

from loguru import logger
from sqlalchemy.orm import Session

from backend.database.connection import init_db
from backend.database.session import SessionLocal
from backend.database.models import ClassroomPhrase, Language, User
from backend.auth.security import get_password_hash

LANGUAGES_SEED_DATA = [
    {"code": "en", "name": "English", "native_name": "English", "script": "Latin", "region": "Pan-India", "is_active": True},
    {"code": "hi", "name": "Hindi", "native_name": "हिन्दी", "script": "Devanagari", "region": "Northern", "is_active": True},
    {"code": "ta", "name": "Tamil", "native_name": "தமிழ்", "script": "Tamil", "region": "Southern", "is_active": True},
    {"code": "ml", "name": "Malayalam", "native_name": "മലയാളം", "script": "Malayalam", "region": "Southern", "is_active": True},
    {"code": "te", "name": "Telugu", "native_name": "తెలుగు", "script": "Telugu", "region": "Southern", "is_active": True},
    {"code": "kn", "name": "Kannada", "native_name": "ಕನ್ನಡ", "script": "Kannada", "region": "Southern", "is_active": True},
    {"code": "sat", "name": "Santhali", "native_name": "ᱥᱟᱱᱛᱟᱲᱤ", "script": "Ol Chiki", "region": "Eastern / Tribal", "is_active": True},
    {"code": "hoc", "name": "Ho", "native_name": "𑢹𑣉𑣉 𑣎𑣋𑣜", "script": "Warang Citi", "region": "Eastern / Tribal", "is_active": True},
    {"code": "unr", "name": "Mundari", "native_name": "ᱢᱩᱱᱰᱟᱨᱤ", "script": "Nag Mundari", "region": "Eastern / Tribal", "is_active": True},
    {"code": "bn", "name": "Bengali", "native_name": "বাংলা", "script": "Bengali", "region": "Eastern", "is_active": True},
    {"code": "mr", "name": "Marathi", "native_name": "मराठी", "script": "Devanagari", "region": "Western", "is_active": True},
]

CLASSROOM_PHRASES_DATA = [
    {
        "category": "greetings",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "வணக்கம் மாணவர்களே",
        "target_text": "നമസ്കാരം വിദ്യാർത്ഥികളെ",
    },
    {
        "category": "instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "உங்கள் புத்தகங்களைத் திறக்கவும்",
        "target_text": "നിങ്ങളുടെ പുസ്തകങ്ങൾ തുറക്കുക",
    },
    {
        "category": "instructions",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "அனைவரும் கவனியுங்கள்",
        "target_text": "എല്ലാവരും ശ്രദ്ധിക്കുക",
    },
    {
        "category": "fln_math",
        "source_language": "ta",
        "target_language": "ml",
        "source_text": "ஒன்று, இரண்டு, மூன்று",
        "target_text": "ഒന്ന്, രണ്ട്, മൂന്ന്",
    },
    {
        "category": "greetings",
        "source_language": "hi",
        "target_language": "ta",
        "source_text": "नमस्ते बच्चों",
        "target_text": "வணக்கம் குழந்தைகளே",
    },
    {
        "category": "greetings",
        "source_language": "en",
        "target_language": "hi",
        "source_text": "Good morning students",
        "target_text": "सुप्रभात छात्रों",
    },
]


def seed_database(db: Session = None) -> tuple[int, int]:
    """
    Seed initial languages, default admin user, and classroom phrases.
    Returns (languages_count, phrases_count).
    """
    close_session = False
    if db is None:
        db = SessionLocal()
        close_session = True

    languages_added = 0
    phrases_added = 0

    try:
        # 1. Seed Languages
        for lang_dict in LANGUAGES_SEED_DATA:
            existing = db.query(Language).filter(Language.code == lang_dict["code"]).first()
            if not existing:
                lang = Language(
                    code=lang_dict["code"],
                    name=lang_dict["name"],
                    native_name=lang_dict["native_name"],
                    script=lang_dict["script"],
                    region=lang_dict["region"],
                    is_active=lang_dict["is_active"],
                )
                db.add(lang)
                languages_added += 1

        # 2. Seed Default Admin/Teacher User if none exists
        admin_user = db.query(User).filter(User.email == "admin@translara.org").first()
        if not admin_user:
            admin = User(
                name="TRANSLARA Master Admin",
                email="admin@translara.org",
                password_hash=get_password_hash("TranslaraAdmin2026!"),
                role="admin",
                preferred_source_lang="ta",
                preferred_target_lang="ml",
            )
            db.add(admin)

        # 3. Seed Classroom Phrases
        for phrase_dict in CLASSROOM_PHRASES_DATA:
            existing = (
                db.query(ClassroomPhrase)
                .filter(
                    ClassroomPhrase.source_language == phrase_dict["source_language"],
                    ClassroomPhrase.target_language == phrase_dict["target_language"],
                    ClassroomPhrase.source_text == phrase_dict["source_text"],
                )
                .first()
            )
            if not existing:
                p = ClassroomPhrase(
                    category=phrase_dict["category"],
                    source_language=phrase_dict["source_language"],
                    target_language=phrase_dict["target_language"],
                    source_text=phrase_dict["source_text"],
                    target_text=phrase_dict["target_text"],
                )
                db.add(p)
                phrases_added += 1

        db.commit()
        logger.info(f"Database seeding complete: {languages_added} languages added, {phrases_added} phrases added.")
        return languages_added, phrases_added
    except Exception as e:
        db.rollback()
        logger.error(f"Seeding error: {e}")
        return 0, 0
    finally:
        if close_session:
            db.close()


if __name__ == "__main__":
    init_db()
    l_cnt, p_cnt = seed_database()
    print(f"TRANSLARA Database Seeded: {l_cnt} new languages, {p_cnt} new phrases.")
