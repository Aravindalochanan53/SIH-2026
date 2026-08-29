"""
Model Manager for TRANSLARA.

Supervises lifecycle, health checking, and memory offloading of ML models.
"""
from __future__ import annotations

from typing import Optional
from loguru import logger

from backend.ml_engine.asr import BaseASR, get_asr_backend
from backend.ml_engine.entity_lock import EntityLock, get_entity_lock
from backend.ml_engine.nmt import BaseNMT, get_nmt_backend
from backend.ml_engine.tts import BaseTTS, get_tts_backend
from backend.schemas import SubsystemStatus


class ModelManager:
    _instance: Optional[ModelManager] = None

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def initialize(self) -> None:
        if getattr(self, "_initialized", False):
            return
        logger.info("Initializing TRANSLARA Model Manager...")
        self._asr: BaseASR = get_asr_backend()
        self._entity_lock: EntityLock = get_entity_lock()
        self._nmt: BaseNMT = get_nmt_backend()
        self._tts: BaseTTS = get_tts_backend()
        self._initialized = True
        logger.info("TRANSLARA Model Manager initialized successfully.")

    def get_status(self) -> dict[str, SubsystemStatus]:
        return {
            "asr": SubsystemStatus.READY if hasattr(self, "_asr") else SubsystemStatus.MOCK,
            "nmt": SubsystemStatus.READY if hasattr(self, "_nmt") else SubsystemStatus.MOCK,
            "tts": SubsystemStatus.READY if hasattr(self, "_tts") else SubsystemStatus.MOCK,
            "entity_lock": SubsystemStatus.READY if hasattr(self, "_entity_lock") else SubsystemStatus.READY,
        }


def get_model_manager() -> ModelManager:
    mgr = ModelManager()
    mgr.initialize()
    return mgr
