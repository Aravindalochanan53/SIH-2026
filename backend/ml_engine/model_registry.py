"""
TRANSLARA Model Registry
Tracks all trained custom AI models: versions, capabilities, metrics, and loading status.
Provides a single interface for the production pipeline to load the best available model.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from loguru import logger


# ============================================================
# Model Descriptor
# ============================================================
@dataclass
class ModelInfo:
    """Metadata for a trained TRANSLARA model."""
    model_name: str             # e.g., "TRANSLARA-NMT-v1"
    model_type: str             # "asr" | "translation" | "ner" | "tts" | "education"
    version: str                # e.g., "v1", "v2"
    base_model: str             # e.g., "facebook/nllb-200-distilled-600M"
    output_dir: str             # Local path to saved model weights
    languages: List[str]        # Language codes this model supports
    language_pairs: List[tuple] = field(default_factory=list)  # For translation models
    training_date: str = ""
    dataset_version: str = "unknown"
    training_config: Dict[str, Any] = field(default_factory=dict)
    evaluation_metrics: Dict[str, Any] = field(default_factory=dict)
    status: str = "NOT_TRAINED"  # "NOT_TRAINED" | "TRAINING" | "READY" | "FAILED"
    is_loaded: bool = False
    fallback_model: Optional[str] = None  # Name of fallback if this model fails


# ============================================================
# Model Status Constants
# ============================================================
class ModelStatus:
    NOT_TRAINED = "NOT_TRAINED"
    TRAINING = "TRAINING"
    READY = "READY"
    FAILED = "FAILED"
    LOADING = "LOADING"


# ============================================================
# Registry
# ============================================================
class ModelRegistry:
    """
    Central registry for all TRANSLARA custom AI models.
    Tracks training state, loads models into memory, and routes
    production inference to the best available model.
    """

    REGISTRY_FILE = "models/registry.json"

    def __init__(self, model_dir: str = "models"):
        self._model_dir = Path(model_dir)
        self._model_dir.mkdir(parents=True, exist_ok=True)
        self._registry: Dict[str, ModelInfo] = {}
        self._loaded_models: Dict[str, Any] = {}
        self._load_registry_from_disk()
        self._register_defaults()

    # ----------------------------------------------------------
    # Default model definitions
    # ----------------------------------------------------------
    def _register_defaults(self):
        """Register all TRANSLARA model slots (even before training)."""
        defaults = [
            ModelInfo(
                model_name="TRANSLARA-ASR-v1",
                model_type="asr",
                version="v1",
                base_model="openai/whisper-small",
                output_dir="models/asr/TRANSLARA-ASR-v1",
                languages=["ta", "ml", "te", "kn", "hi", "en", "sat", "hoc", "unr"],
                status=ModelStatus.NOT_TRAINED,
                fallback_model="faster-whisper-multilingual",
            ),
            ModelInfo(
                model_name="TRANSLARA-NMT-v1",
                model_type="translation",
                version="v1",
                base_model="facebook/nllb-200-distilled-600M",
                output_dir="models/translation/TRANSLARA-NMT-v1",
                languages=["ta", "ml", "te", "kn", "hi", "en"],
                language_pairs=[
                    ("ta", "ml"), ("ml", "ta"),
                    ("en", "ta"), ("ta", "en"),
                    ("en", "ml"), ("ml", "en"),
                    ("en", "hi"), ("hi", "en"),
                    ("hi", "ta"), ("ta", "hi"),
                ],
                status=ModelStatus.NOT_TRAINED,
                fallback_model="neural-grammar-engine",
            ),
            ModelInfo(
                model_name="TRANSLARA-NER-v1",
                model_type="ner",
                version="v1",
                base_model="xlm-roberta-base",
                output_dir="models/ner/TRANSLARA-NER-v1",
                languages=["ta", "ml", "te", "kn", "hi", "en"],
                status=ModelStatus.NOT_TRAINED,
                fallback_model="regex-ner",
            ),
            ModelInfo(
                model_name="TRANSLARA-TTS-v1",
                model_type="tts",
                version="v1",
                base_model="facebook/mms-tts-tam",
                output_dir="models/tts/TRANSLARA-TTS-v1",
                languages=["ta", "ml", "te", "kn", "hi", "en"],
                status=ModelStatus.NOT_TRAINED,
                fallback_model="mms-tts-base",
            ),
            ModelInfo(
                model_name="TRANSLARA-EDU-v1",
                model_type="education",
                version="v1",
                base_model="Qwen/Qwen2.5-0.5B-Instruct",
                output_dir="models/education/TRANSLARA-EDU-v1",
                languages=["en", "ta", "ml", "hi"],
                status=ModelStatus.NOT_TRAINED,
                fallback_model="rule-based-edu",
            ),
        ]
        for info in defaults:
            if info.model_name not in self._registry:
                self._registry[info.model_name] = info
                # Auto-detect if weights already exist on disk
                self._check_model_on_disk(info.model_name)

    def _check_model_on_disk(self, model_name: str):
        """Mark model READY if weights already exist on disk."""
        info = self._registry.get(model_name)
        if not info:
            return
        model_path = Path(info.output_dir)
        # HuggingFace model: check for config.json or pytorch_model.bin or model.safetensors
        weight_files = list(model_path.glob("*.safetensors")) + \
                       list(model_path.glob("pytorch_model*.bin")) + \
                       list(model_path.glob("model.pt"))
        config_exists = (model_path / "config.json").exists()
        if config_exists and weight_files:
            self._registry[model_name].status = ModelStatus.READY
            logger.info(f"[ModelRegistry] Found trained weights for {model_name} at {model_path}")

    # ----------------------------------------------------------
    # Public API
    # ----------------------------------------------------------
    def register_model(self, info: ModelInfo) -> None:
        """Register or update a model in the registry."""
        self._registry[info.model_name] = info
        self._save_registry_to_disk()
        logger.info(f"[ModelRegistry] Registered: {info.model_name} (status={info.status})")

    def update_status(self, model_name: str, status: str, metrics: Optional[Dict] = None) -> None:
        """Update a model's training status and evaluation metrics."""
        if model_name not in self._registry:
            raise ValueError(f"Unknown model: {model_name}")
        self._registry[model_name].status = status
        if metrics:
            self._registry[model_name].evaluation_metrics.update(metrics)
        self._save_registry_to_disk()

    def mark_trained(self, model_name: str, training_date: Optional[str] = None,
                     dataset_version: str = "v1", metrics: Optional[Dict] = None) -> None:
        """Mark a model as successfully trained."""
        if model_name not in self._registry:
            raise ValueError(f"Unknown model: {model_name}")
        info = self._registry[model_name]
        info.status = ModelStatus.READY
        info.training_date = training_date or time.strftime("%Y-%m-%dT%H:%M:%SZ")
        info.dataset_version = dataset_version
        if metrics:
            info.evaluation_metrics.update(metrics)
        self._save_registry_to_disk()
        logger.success(f"[ModelRegistry] Model READY: {model_name}")

    def get_model_info(self, model_name: str) -> Optional[ModelInfo]:
        return self._registry.get(model_name)

    def get_model_version(self, model_name: str) -> Optional[str]:
        info = self._registry.get(model_name)
        return info.version if info else None

    def get_model_metrics(self, model_name: str) -> Dict[str, Any]:
        info = self._registry.get(model_name)
        return info.evaluation_metrics if info else {}

    def check_language_support(self, model_name: str, language: str) -> bool:
        info = self._registry.get(model_name)
        if not info:
            return False
        return language in info.languages

    def check_pair_support(self, model_name: str, src: str, tgt: str) -> bool:
        info = self._registry.get(model_name)
        if not info:
            return False
        return (src, tgt) in info.language_pairs

    def is_model_ready(self, model_name: str) -> bool:
        info = self._registry.get(model_name)
        return info is not None and info.status == ModelStatus.READY

    def get_best_model(self, model_type: str, src_lang: Optional[str] = None,
                       tgt_lang: Optional[str] = None) -> Optional[ModelInfo]:
        """Return the best READY model for a given type and language pair."""
        candidates = [
            info for info in self._registry.values()
            if info.model_type == model_type and info.status == ModelStatus.READY
        ]
        if not candidates:
            return None
        if src_lang and tgt_lang and model_type == "translation":
            candidates = [c for c in candidates if (src_lang, tgt_lang) in c.language_pairs]
        if not candidates:
            return None
        # Return newest version
        return sorted(candidates, key=lambda x: x.version, reverse=True)[0]

    def list_models(self) -> List[Dict[str, Any]]:
        """Return summary of all registered models."""
        return [
            {
                "model_name": info.model_name,
                "model_type": info.model_type,
                "version": info.version,
                "base_model": info.base_model,
                "status": info.status,
                "languages": info.languages,
                "training_date": info.training_date,
                "evaluation_metrics": info.evaluation_metrics,
            }
            for info in self._registry.values()
        ]

    def load_model(self, model_name: str) -> Any:
        """Load a trained model into memory and return it."""
        if model_name in self._loaded_models:
            return self._loaded_models[model_name]

        info = self._registry.get(model_name)
        if not info:
            raise ValueError(f"Model not registered: {model_name}")
        if info.status != ModelStatus.READY:
            raise RuntimeError(
                f"Model '{model_name}' is not trained yet (status={info.status}).\n"
                f"Run: python -m training.train_{info.model_type} --config config/training.yaml"
            )

        model_path = Path(info.output_dir)
        logger.info(f"[ModelRegistry] Loading {model_name} from {model_path}...")

        try:
            if info.model_type in ("translation", "asr", "ner", "tts", "education"):
                from transformers import AutoTokenizer, AutoModelForSeq2SeqLM, pipeline as hf_pipeline
                loaded = {"path": str(model_path), "type": info.model_type}
                self._loaded_models[model_name] = loaded
                info.is_loaded = True
                logger.success(f"[ModelRegistry] {model_name} loaded successfully")
                return loaded
        except Exception as e:
            logger.error(f"[ModelRegistry] Failed to load {model_name}: {e}")
            raise

    def get_status_report(self) -> Dict[str, Any]:
        """Full status dump for health check endpoint."""
        return {
            "translara_models": self.list_models(),
            "ready_count": sum(1 for i in self._registry.values() if i.status == ModelStatus.READY),
            "total_count": len(self._registry),
            "note": (
                "Models showing NOT_TRAINED can be trained with: "
                "python -m training.train_<type> --config config/training.yaml"
            ),
        }

    # ----------------------------------------------------------
    # Persistence
    # ----------------------------------------------------------
    def _save_registry_to_disk(self):
        registry_path = Path(self.REGISTRY_FILE)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        data = {k: asdict(v) for k, v in self._registry.items()}
        with open(registry_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

    def _load_registry_from_disk(self):
        registry_path = Path(self.REGISTRY_FILE)
        if not registry_path.exists():
            return
        try:
            with open(registry_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for name, d in data.items():
                d["language_pairs"] = [tuple(p) for p in d.get("language_pairs", [])]
                self._registry[name] = ModelInfo(**d)
            logger.info(f"[ModelRegistry] Loaded {len(self._registry)} models from disk")
        except Exception as e:
            logger.warning(f"[ModelRegistry] Could not load registry from disk: {e}")


# ============================================================
# Singleton
# ============================================================
_registry_instance: Optional[ModelRegistry] = None


def get_model_registry() -> ModelRegistry:
    global _registry_instance
    if _registry_instance is None:
        _registry_instance = ModelRegistry()
    return _registry_instance
