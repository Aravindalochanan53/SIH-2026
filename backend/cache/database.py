"""
SQLAlchemy Database Engine and Session Factory.
"""
from __future__ import annotations

from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from backend.config import settings

# Ensure sqlite parent directory exists
cache_url = settings.offline_db_url
if cache_url.startswith("sqlite:///"):
    db_path = cache_url.replace("sqlite:///", "")
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)

engine = create_engine(
    cache_url,
    connect_args={"check_same_thread": False} if cache_url.startswith("sqlite") else {},
    echo=False,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI Dependency for database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables."""
    from backend.cache import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
