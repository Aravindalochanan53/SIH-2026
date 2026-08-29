"""
TRANSLARA-TTS Fine-Tuning Script
Fine-tunes Facebook MMS-TTS VITS models on custom Indian language voice data.

Usage:
    python -m training.train_tts --config config/training.yaml --language ta
    python -m training.train_tts --config config/training.yaml --dry-run

Base models (per language):
    ta  → facebook/mms-tts-tam
    ml  → facebook/mms-tts-mal
    te  → facebook/mms-tts-tel
    kn  → facebook/mms-tts-kan
    hi  → facebook/mms-tts-hin
    en  → facebook/mms-tts-eng

Dataset format (CSV):
    text,audio_path,language,speaker_id
    வணக்கம் மாணவர்களே,data/tts/train/ta/speaker1_001.wav,ta,speaker1
    Hello students,data/tts/train/en/speaker2_001.wav,en,speaker2

Output: models/tts/TRANSLARA-TTS-v1/<lang>/
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


MMS_TTS_MODELS = {
    "ta": "facebook/mms-tts-tam",
    "ml": "facebook/mms-tts-mal",
    "te": "facebook/mms-tts-tel",
    "kn": "facebook/mms-tts-kan",
    "hi": "facebook/mms-tts-hin",
    "en": "facebook/mms-tts-eng",
}


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TRANSLARA-TTS Fine-Tuning (MMS-TTS VITS)")
    p.add_argument("--config", type=str, default="config/training.yaml")
    p.add_argument("--language", type=str, required=False,
                   help="Language to train (ta/ml/te/kn/hi/en). Trains all if not set.")
    p.add_argument("--dry-run", action="store_true")
    p.add_argument("--resume", type=str, default=None)
    p.add_argument("--epochs", type=int, default=None)
    return p.parse_args()


def detect_device(config_device: str = "auto") -> str:
    if config_device != "auto":
        return config_device
    try:
        import torch
        if torch.cuda.is_available():
            return "cuda"
    except ImportError:
        pass
    return "cpu"


# ============================================================
# Dataset
# ============================================================
@dataclass
class TTSSample:
    text: str
    audio_path: str
    language: str
    speaker_id: str = "default"


def load_tts_dataset(data_dir: str, language_filter: Optional[str] = None) -> List[TTSSample]:
    """
    Load TTS dataset from CSV manifest.

    CSV columns: text, audio_path, language, speaker_id
    Place WAV files at 22050 Hz or 16000 Hz mono.
    """
    samples = []
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv")) + list(data_path.glob("**/*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}.\n\n"
            f"Expected CSV columns: text,audio_path,language,speaker_id\n"
            f"Example row: வணக்கம்,data/tts/train/ta/001.wav,ta,speaker1\n\n"
            f"Run: python scripts/prepare_tts_dataset.py --demo"
        )

    for csv_file in csv_files:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lang = row.get("language", "").strip()
                if language_filter and lang != language_filter:
                    continue
                text = row.get("text", "").strip()
                audio = row.get("audio_path", "").strip()
                speaker = row.get("speaker_id", "default").strip()
                if text and audio:
                    samples.append(TTSSample(text, audio, lang, speaker))

    logger.info(f"[TTS-Dataset] Loaded {len(samples)} samples from {data_dir}")
    return samples


def validate_tts_dataset(samples: List[TTSSample]) -> Dict:
    missing = [s.audio_path for s in samples if not Path(s.audio_path).exists()]
    empty = [s for s in samples if not s.text.strip()]
    by_lang = {}
    for s in samples:
        by_lang[s.language] = by_lang.get(s.language, 0) + 1
    return {
        "total": len(samples),
        "valid": len(samples) - len(missing) - len(empty),
        "missing_audio": len(missing),
        "empty_text": len(empty),
        "by_language": by_lang,
    }


# ============================================================
# Training (per language)
# ============================================================
def train_language(
    language: str,
    samples: List[TTSSample],
    val_samples: List[TTSSample],
    config: Dict,
    device: str,
    args: argparse.Namespace,
):
    """Fine-tune MMS-TTS VITS for a single language."""
    try:
        import torch
        from transformers import (
            VitsModel,
            VitsTokenizer,
            TrainingArguments,
            Trainer,
        )
        from datasets import Dataset, Audio
    except ImportError as e:
        raise ImportError(
            f"Missing: {e}\n"
            f"pip install transformers>=4.40.0 datasets soundfile librosa"
        )

    cfg = config["tts"]
    base_models = cfg.get("base_models", MMS_TTS_MODELS)
    base_model = base_models.get(language)

    if not base_model:
        logger.warning(
            f"[TTS-Train] No base MMS-TTS model for language '{language}'.\n"
            f"  Languages sat/hoc/unr require data collection + full VITS training.\n"
            f"  Skipping {language} for now."
        )
        return

    output_dir = str(Path(cfg["output_dir"]) / language)
    num_epochs = args.epochs or cfg["num_train_epochs"]

    logger.info(f"[TTS-Train] Language: {language}")
    logger.info(f"[TTS-Train] Base:     {base_model}")
    logger.info(f"[TTS-Train] Output:   {output_dir}")
    logger.info(f"[TTS-Train] Samples:  {len(samples)} train | {len(val_samples)} val")

    # Load tokenizer and model
    tokenizer = VitsTokenizer.from_pretrained(base_model)
    model = VitsModel.from_pretrained(base_model)
    if device != "cpu":
        model = model.to(device)

    # Build dataset
    def preprocess(batch):
        text_inputs = tokenizer(batch["text"], return_tensors="pt", padding=True)
        batch["input_ids"] = text_inputs["input_ids"]
        batch["attention_mask"] = text_inputs["attention_mask"]
        return batch

    train_dict = {
        "text": [s.text for s in samples],
        "audio": [s.audio_path for s in samples],
    }
    val_dict = {
        "text": [s.text for s in val_samples],
        "audio": [s.audio_path for s in val_samples],
    }

    train_ds = Dataset.from_dict(train_dict).cast_column("audio", Audio(sampling_rate=cfg["sampling_rate"]))
    val_ds = Dataset.from_dict(val_dict).cast_column("audio", Audio(sampling_rate=cfg["sampling_rate"]))

    train_ds = train_ds.map(preprocess, batched=True, remove_columns=["audio"])
    val_ds = val_ds.map(preprocess, batched=True, remove_columns=["audio"])

    fp16 = config.get("fp16", False) and device == "cuda"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        fp16=fp16,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        logging_steps=50,
        load_best_model_at_end=True,
        report_to="none",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
    )

    logger.info(f"[TTS-Train] 🚀 Training TTS for {language}...")
    trainer.train(resume_from_checkpoint=args.resume)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    with open(Path(output_dir) / "training_metrics.json", "w") as mf:
        json.dump({
            "language": language,
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "train_samples": len(samples),
        }, mf, indent=2)

    logger.success(f"[TTS-Train] ✅ {language} TTS model saved to {output_dir}")


# ============================================================
# Entry Point
# ============================================================
def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    device = detect_device(config.get("device", "auto"))
    cfg = config["tts"]
    languages_to_train = [args.language] if args.language else list(MMS_TTS_MODELS.keys())

    logger.info("=" * 60)
    logger.info("  TRANSLARA-TTS Fine-Tuning (MMS-TTS VITS)")
    logger.info(f"  Languages: {languages_to_train}")
    logger.info(f"  Device:    {device}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[TTS-Train] DRY RUN")
        for lang in languages_to_train:
            try:
                samples = load_tts_dataset(cfg["train_data"], lang)
                report = validate_tts_dataset(samples)
                logger.info(f"[TTS-Train] {lang}: {json.dumps(report, indent=2)}")
            except FileNotFoundError as e:
                logger.error(str(e))
        return

    for lang in languages_to_train:
        train_samples = load_tts_dataset(cfg["train_data"], lang)
        val_samples = load_tts_dataset(cfg["validation_data"], lang)
        if not train_samples:
            logger.warning(f"[TTS-Train] No training samples for {lang}, skipping")
            continue
        train_language(lang, train_samples, val_samples, config, device, args)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.ml_engine.model_registry import get_model_registry
        get_model_registry().mark_trained("TRANSLARA-TTS-v1", dataset_version="v1")
    except Exception as e:
        logger.warning(f"[TTS-Train] Registry update failed: {e}")


if __name__ == "__main__":
    main()
