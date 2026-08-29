"""
FastAPI Dependencies for TRANSLARA.
"""
from typing import Generator
from sqlalchemy.orm import Session

from backend.cache.database import get_db
from backend.cache.offline_store import OfflineStore, get_offline_store
from backend.ml_engine.entity_lock import EntityLock, get_entity_lock
from backend.ml_engine.model_manager import ModelManager, get_model_manager


def get_entity_lock_dep() -> EntityLock:
    return get_entity_lock()


def get_model_manager_dep() -> ModelManager:
    return get_model_manager()


def get_offline_store_dep() -> OfflineStore:
    return get_offline_store()
