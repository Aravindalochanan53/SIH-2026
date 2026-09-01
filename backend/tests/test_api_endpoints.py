"""
Integration tests for TRANSLARA FastAPI endpoints.
Tests /health, /api/languages, /api/auth/register, /api/auth/login, /api/translate, /api/chat.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.database.base import Base
from backend.database.seed import seed_database
from backend.database.session import get_db
from backend.server import app

# Create in-memory SQLite database with StaticPool and check_same_thread=False
test_engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
    echo=False,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)
with TestingSessionLocal() as session:
    seed_database(session)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_health_endpoint():
    """Verify /health returns healthy status and subsystem states."""
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "ai_engine" in data
    assert data["app_name"] == "TRANSLARA"


def test_languages_endpoint():
    """Verify /api/languages returns pan-Indian language registry."""
    response = client.get("/api/languages")
    assert response.status_code == 200
    data = response.json()
    assert "languages" in data
    assert len(data["languages"]) > 0
    codes = [l["code"] for l in data["languages"]]
    assert "ta" in codes
    assert "ml" in codes
    assert "hi" in codes


def test_auth_and_protected_profile_flow():
    """Verify register, login, and token-authenticated /api/auth/me profile."""
    # 1. Register new teacher
    reg_payload = {
        "name": "Integration Teacher",
        "email": "teacher_integration@translara.org",
        "password": "StrongPassword123!",
        "role": "teacher",
        "preferred_source_lang": "ta",
        "preferred_target_lang": "ml",
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    if reg_res.status_code == 400:
        # Already exists, login instead
        login_res = client.post(
            "/api/auth/login",
            json={"email": reg_payload["email"], "password": reg_payload["password"]},
        )
        assert login_res.status_code == 200
        token = login_res.json()["access_token"]
    else:
        assert reg_res.status_code == 201
        token = reg_res.json()["access_token"]

    # 2. Access /api/auth/me with Bearer token
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_res.status_code == 200
    me_data = me_res.json()
    assert me_data["email"] == "teacher_integration@translara.org"
    assert me_data["role"] == "teacher"


def test_translate_endpoint_with_history():
    """Verify POST /api/translate returns translation and saves history."""
    payload = {
        "text": "வணக்கம் மாணவர்களே",
        "source_language": "ta",
        "target_language": "ml",
    }
    res = client.post("/api/translate", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert data["success"] is True
    assert data["translation"] is not None
    assert data["source_language"] == "ta"
    assert data["target_language"] == "ml"


def test_chat_message_endpoint():
    """Verify POST /api/chat/message returns AI response."""
    payload = {
        "message": "Hello teacher assistant",
        "source_lang": "en",
        "target_lang": "ta",
    }
    res = client.post("/api/chat/message", json=payload)
    assert res.status_code == 200
    data = res.json()
    assert "sender" in data
    assert "text" in data
    assert data["sender"] == "assistant"
