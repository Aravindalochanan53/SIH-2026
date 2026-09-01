"""
TRANSLARA Database Connection.

Primary database:
    Microsoft SQL Server (MSSQL) using SQLAlchemy + pyodbc.

Offline database:
    SQLite is available only when explicitly configured.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from loguru import logger
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from backend.config import settings
from backend.database.base import Base


# Global engine (lazy-initialized)
_engine: Optional[Engine] = None


def _build_engine() -> Engine:
    """
    Build the SQLAlchemy database engine.

    TRANSLARA uses MSSQL as the primary database.
    SQLite is used only when the configured URL explicitly starts
    with 'sqlite:///'.
    """

    database_url = settings.get_database_url()

    logger.info(f"Database URL scheme: {database_url.split(':', 1)[0]}")

    # ---------------------------------------------------------
    # MSSQL
    # ---------------------------------------------------------
    if database_url.startswith("mssql+pyodbc://"):
        try:
            import pyodbc

            available_drivers = pyodbc.drivers()

            logger.info(
                f"Available SQL Server ODBC drivers: {available_drivers}"
            )

            if settings.db_driver not in available_drivers:
                raise RuntimeError(
                    f"Required ODBC driver '{settings.db_driver}' "
                    f"is not installed. Available drivers: "
                    f"{available_drivers}"
                )

            eng = create_engine(
                database_url,
                pool_pre_ping=True,
                pool_size=10,
                max_overflow=20,
                pool_recycle=1800,
                pool_timeout=30,
                connect_args={
                    "timeout": 10,
                },
                echo=False,
            )

            # IMPORTANT:
            # Actually test the connection here.
            with eng.connect() as connection:
                connection.execute(text("SELECT 1"))

            logger.info(
                "MSSQL SQLAlchemy engine initialized and connection verified."
            )

            return eng

        except Exception as exc:
            logger.error(
                f"MSSQL database connection failed: {exc}"
            )

            # DO NOT silently fall back to SQLite.
            raise RuntimeError(
                "TRANSLARA could not connect to MSSQL. "
                "Check DB_SERVER, DB_NAME, ODBC driver and Windows Authentication."
            ) from exc

    # ---------------------------------------------------------
    # SQLite
    # ---------------------------------------------------------
    if database_url.startswith("sqlite:///"):
        logger.warning(
            "TRANSLARA is running with SQLite instead of MSSQL."
        )

        eng = create_engine(
            database_url,
            connect_args={
                "check_same_thread": False,
            },
            pool_pre_ping=True,
            echo=False,
        )

        return eng

    # ---------------------------------------------------------
    # Unsupported database
    # ---------------------------------------------------------
    raise RuntimeError(
        f"Unsupported database URL: {database_url}"
    )


def get_engine() -> Engine:
    """
    Get or lazily create the global SQLAlchemy engine.

    This avoids crashing at module import time if the database
    is not yet available (e.g. during test collection or CLI commands).
    """
    global _engine
    if _engine is None:
        _engine = _build_engine()
    return _engine


# Backward compatibility alias
engine = property(lambda self: get_engine())


def check_db_health() -> Dict[str, Any]:
    """
    Check whether the configured database is reachable.
    """

    try:
        eng = get_engine()
        with eng.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "dialect": eng.dialect.name,
            "driver": eng.url.drivername,
        }

    except Exception as exc:
        logger.error(
            f"Database health check failed: {exc}"
        )

        return {
            "status": "disconnected",
            "dialect": "unknown",
            "error": str(exc),
        }


def init_db() -> None:
    """
    Create all SQLAlchemy models/tables.
    """

    # Import models so SQLAlchemy registers all tables.
    from backend.database import models  # noqa: F401

    try:
        eng = get_engine()
        Base.metadata.create_all(bind=eng)

        logger.info(
            "TRANSLARA database tables verified/created successfully."
        )

    except Exception as exc:
        logger.error(
            f"Failed to initialize database tables: {exc}"
        )
        raise