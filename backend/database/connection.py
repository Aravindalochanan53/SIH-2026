"""
Database connection and session factory for TRANSLARA.
Supports Microsoft SQL Server (MSSQL) with automatic fallback to SQLite for portable offline operation.
"""
from __future__ import annotations

import os
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from loguru import logger

from backend.config import settings

Base = declarative_base()

# Construct database URL: MSSQL or SQLite
db_url = os.getenv("DATABASE_URL", settings.database_url)

# Handle engine creation with MSSQL or SQLite connection pooling parameters
try:
    if db_url.startswith("sqlite"):
        engine = create_engine(
            db_url,
            connect_args={"check_same_thread": False},
            echo=False,
        )
    else:
        # MSSQL engine
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
            echo=False,
        )
    logger.info(f"Database engine initialized with driver: {engine.url.drivername}")
except Exception as e:
    logger.warning(f"Failed to initialize primary database URL ({e}); falling back to local SQLite.")
    db_path = Path("./data/translara.db")
    db_path.parent.mkdir(parents=True, exist_ok=True)
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
        echo=False,
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """FastAPI Dependency for database session management."""
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all database tables."""
    Base.metadata.create_all(bind=engine)
