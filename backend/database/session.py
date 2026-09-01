"""
Session factory and FastAPI dependencies for TRANSLARA Database.
"""
from typing import Generator
from sqlalchemy.orm import sessionmaker, Session
from backend.database.connection import get_engine


def _get_session_factory():
    """Create a sessionmaker bound to the lazily-initialized engine."""
    return sessionmaker(autocommit=False, autoflush=False, bind=get_engine())


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency for database session management.
    Yields an active database session and ensures clean closure.
    """
    SessionLocal = _get_session_factory()
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# For backward compatibility — callers that import SessionLocal directly
class _LazySessionLocal:
    """Lazy proxy that creates the real sessionmaker on first call."""
    _factory = None

    def __call__(self, *args, **kwargs):
        if self._factory is None:
            self._factory = _get_session_factory()
        return self._factory(*args, **kwargs)

    def __getattr__(self, name):
        if self._factory is None:
            self._factory = _get_session_factory()
        return getattr(self._factory, name)


SessionLocal = _LazySessionLocal()
