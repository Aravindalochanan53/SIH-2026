"""
Automated Test Suite for TRANSLARA MSSQL Database Integration, Unicode Safety, and Authentication.
"""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.auth.security import create_access_token, decode_access_token, get_password_hash, verify_password
from backend.database.base import Base
from backend.database.models import (
    ChatMessage,
    ChatSession,
    ClassroomPhrase,
    EntityRecord,
    Flashcard,
    Language,
    Translation,
    TranslationHistory,
    User,
    VideoJob,
    Worksheet,
)
from backend.database.repositories.chat_and_pedagogy_repo import ChatRepository, PedagogyRepository
from backend.database.repositories.translation_repo import TranslationRepository
from backend.database.seed import seed_database


@pytest.fixture(scope="module")
def test_db():
    """Create in-memory SQLite database simulating relational SQL Server schema."""
    engine = create_engine("sqlite:///:memory:", echo=False)
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_password_hashing():
    """Verify password hashing with bcrypt and secure verification."""
    password = "SecurePassword123!"
    hashed = get_password_hash(password)
    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


def test_jwt_token_generation_and_validation():
    """Verify JWT token encoding and decoding."""
    token = create_access_token(subject=1, role="teacher")
    assert isinstance(token, str)
    payload = decode_access_token(token)
    assert payload is not None
    assert payload["sub"] == "1"
    assert payload["role"] == "teacher"


def test_database_seeding(test_db):
    """Verify database seeding seeds all Indian languages and classroom phrases."""
    l_cnt, p_cnt = seed_database(test_db)
    assert l_cnt > 0
    assert p_cnt > 0

    # Verify Tamil language exists
    ta = test_db.query(Language).filter(Language.code == "ta").first()
    assert ta is not None
    assert ta.name == "Tamil"
    assert ta.native_name == "தமிழ்"

    # Verify Malayalam exists
    ml = test_db.query(Language).filter(Language.code == "ml").first()
    assert ml is not None
    assert ml.name == "Malayalam"
    assert ml.native_name == "മലയാളം"


def test_unicode_multilingual_storage(test_db):
    """
    Test storing and retrieving all supported Indian vernacular languages:
    Tamil, Malayalam, Telugu, Kannada, Hindi, Santhali, Ho, Mundari.
    """
    unicode_samples = [
        {"lang": "ta", "sample": "வணக்கம் மாணவர்களே", "desc": "Tamil"},
        {"lang": "ml", "sample": "നമസ്കാരം വിദ്യാർത്ഥികളെ", "desc": "Malayalam"},
        {"lang": "hi", "sample": "नमस्ते छात्रों", "desc": "Hindi"},
        {"lang": "te", "sample": "నమస్కారం విద్యార్థులు", "desc": "Telugu"},
        {"lang": "kn", "sample": "ನಮಸ್ಕಾರ ವಿದ್ಯಾರ್ಥಿಗಳೇ", "desc": "Kannada"},
        {"lang": "sat", "sample": "ᱡᱚᱦᱟᱨ", "desc": "Santhali"},
        {"lang": "hoc", "sample": "𑢹𑣉𑣉 𑣎𑣋𑣜", "desc": "Ho"},
        {"lang": "unr", "sample": "ᱢᱩᱱᱰᱟᱨᱤ", "desc": "Mundari"},
    ]

    for item in unicode_samples:
        trans = Translation(
            source_language="en",
            target_language=item["lang"],
            source_text="Hello students",
            target_text=item["sample"],
            engine="test_engine",
        )
        test_db.add(trans)
    test_db.commit()

    # Query back and verify Unicode fidelity
    for item in unicode_samples:
        record = (
            test_db.query(Translation)
            .filter(Translation.target_language == item["lang"])
            .first()
        )
        assert record is not None
        assert record.target_text == item["sample"]


def test_user_and_translation_history_isolation(test_db):
    """Test user registration and isolated translation history query."""
    user1 = User(
        name="Teacher Priya",
        email="priya@school.edu",
        password_hash=get_password_hash("PriyaPass123"),
        role="teacher",
    )
    user2 = User(
        name="Teacher Rahul",
        email="rahul@school.edu",
        password_hash=get_password_hash("RahulPass123"),
        role="teacher",
    )
    test_db.add_all([user1, user2])
    test_db.commit()

    repo = TranslationRepository(test_db)
    # Save translation for user1
    repo.save_history(
        user_id=user1.id,
        source_language="ta",
        target_language="ml",
        source_text="வணக்கம்",
        translated_text="നമസ്കാരം",
        latency_ms=120.5,
    )
    # Save translation for user2
    repo.save_history(
        user_id=user2.id,
        source_language="hi",
        target_language="ta",
        source_text="नमस्ते",
        translated_text="வணக்கம்",
        latency_ms=95.0,
    )

    u1_hist = repo.get_history_by_user(user_id=user1.id, is_admin=False)
    assert len(u1_hist) == 1
    assert u1_hist[0].source_text == "வணக்கம்"

    u2_hist = repo.get_history_by_user(user_id=user2.id, is_admin=False)
    assert len(u2_hist) == 1
    assert u2_hist[0].source_text == "नमस्ते"

    all_hist = repo.get_history_by_user(user_id=None, is_admin=True)
    assert len(all_hist) >= 2


def test_chat_sessions_and_messages(test_db):
    """Test ChatSession and ChatMessage relational persistence."""
    chat_repo = ChatRepository(test_db)
    session = chat_repo.get_or_create_session(
        session_id="test_sess_01",
        title="Grade 1 Math Lesson",
        language="ta",
    )
    assert session.id == "test_sess_01"

    # Save user message
    msg1 = chat_repo.save_message(
        session_id=session.id,
        role="user",
        message="எண்களை விளக்குங்கள்",
        language="ta",
    )
    # Save assistant response
    msg2 = chat_repo.save_message(
        session_id=session.id,
        role="assistant",
        message="1 முதல் 5 வரையிலான எண்கள்:",
        language="ta",
    )

    messages = chat_repo.get_messages(session.id)
    assert len(messages) == 2
    assert messages[0].message == "எண்களை விளக்குங்கள்"
    assert messages[1].message == "1 முதல் 5 வரையிலான எண்கள்:"


def test_video_job_repository(test_db):
    """Test VideoJob lifecycle in database."""
    from backend.database.repositories.video_repo import VideoRepository

    v_repo = VideoRepository(test_db)
    job = v_repo.create_job(
        job_id="vjob_100",
        original_filename="science_lesson.mp4",
        source_language="ta",
        target_language="ml",
    )
    assert job.status == "queued"

    updated = v_repo.update_job_status(
        job_id="vjob_100",
        status="completed",
        progress=1.0,
        output_path="/assets/videos/science_lesson_ml.mp4",
    )
    assert updated is not None
    assert updated.status == "completed"
    assert updated.output_path == "/assets/videos/science_lesson_ml.mp4"
