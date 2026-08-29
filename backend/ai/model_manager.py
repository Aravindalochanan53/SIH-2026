"""
Model Manager & Resource Controller for TRANSLARA AI.
Manages lazy loading, GPU/CPU hardware detection, warm-up, and memory clearing.
"""
from __future__ import annotations

import asyncio
import gc
from typing import Any, Dict, Optional
from loguru import logger

from backend.config import settings


class ModelManager:
    """
    Central Manager for AI models:
    - Auto GPU/CPU detection
    - Lazy loading
    - Model warm-up
    - Memory caching & garbage collection
    """

    _instance: Optional[ModelManager] = None

    def __new__(cls) -> ModelManager:
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._models: Dict[str, Any] = {}
            cls._instance._device = cls._instance._detect_device()
        return cls._instance

    @staticmethod
    def _detect_device() -> str:
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                logger.info(f"CUDA GPU detected: {gpu_name}. Enabling accelerated inference.")
                return "cuda"
        except Exception:
            pass
        logger.info("Using CPU device for model inference.")
        return "cpu"

    @property
    def device(self) -> str:
        return self._device

    async def warm_up(self) -> None:
        """Pre-warm critical AI pipelines."""
        logger.info("Pre-warming TRANSLARA AI Engine...")
        try:
            from backend.ai.translation.registry import get_translation_engine
            engine = get_translation_engine()
            # Warm up with a sample translation
            await engine.translate("Hello", "en", "ta")
            logger.info("TRANSLARA AI Engine warm-up completed.")
        except Exception as e:
            logger.warning(f"Engine warm-up notice: {e}")

    def clear_memory(self) -> None:
        """Release unused tensors and execute garbage collection."""
        try:
            import torch
            if torch.cuda.is_available():
                torch.cuda.empty_cache()
        except Exception:
            pass
        gc.collect()
        logger.info("AI Model memory cleared.")


def get_model_manager() -> ModelManager:
    return ModelManager()
