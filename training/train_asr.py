"""
TRANSLARA-ASR Fine-Tuning Script
Fine-tunes OpenAI Whisper on custom Indian language classroom audio data.

Usage:
    python -m training.train_asr --config config/training.yaml
    python -m training.train_asr --config config/training.yaml --dry-run
    python -m training.train_asr --config config/training.yaml --language ta

Base model: openai/whisper-small (CPU-compatible) or whisper-large-v3 (GPU)
Output:     models/asr/TRANSLARA-ASR-v1/
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

# ============================================================
# Argument Parsing
# ============================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TRANSLARA-ASR Fine-Tuning")
    p.add_argument("--config", type=str, default="config/training.yaml",
                   help="Path to training.yaml")
    p.add_argument("--language", type=str, default=None,
                   help="Fine-tune on a specific language only (e.g. 'ta')")
    p.add_argument("--dry-run", action="store_true",
                   help="Validate config and data without running training")
    p.add_argument("--resume", type=str, default=None,
                   help="Path to checkpoint to resume from")
    p.add_argument("--epochs", type=int, default=None,
                   help="Override num_train_epochs from config")
    return p.parse_args()


# ============================================================
# Hardware Detection
# ============================================================
def detect_device(config_device: str = "auto") -> str:
    if config_device != "auto":
        return config_device
    try:
        import torch
        if torch.cuda.is_available():
            device = "cuda"
            logger.info(f"[ASR-Train] CUDA GPU detected: {torch.cuda.get_device_name(0)}")
        elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            device = "mps"
            logger.info("[ASR-Train] Apple MPS detected")
        else:
            device = "cpu"
            logger.warning("[ASR-Train] No GPU found — training on CPU (SLOW for Whisper)")
    except ImportError:
        device = "cpu"
    return device


# ============================================================
# Dataset Loader
# ============================================================
@dataclass
class ASRSample:
    audio_path: str
    transcript: str
    language: str


def load_asr_dataset(data_dir: str, language_filter: Optional[str] = None) -> List[ASRSample]:
    """
    Load ASR dataset from a directory of CSV manifests.

    Expected CSV format:
        audio_file,language,transcript
        data/asr/train/ta/sample_001.wav,ta,வணக்கம் மாணவர்களே
        data/asr/train/ml/sample_002.wav,ml,നമസ്കാരം കുട്ടികളേ

    The audio_file column must be a valid path to a 16kHz mono WAV file.
    """
    samples = []
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv")) + list(data_path.glob("**/*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV manifest files found in {data_dir}.\n"
            f"Expected CSV format:\n"
            f"  audio_file,language,transcript\n"
            f"  data/asr/train/ta/sample_001.wav,ta,வணக்கம்\n\n"
            f"Please provide your audio data and run:\n"
            f"  python scripts/prepare_asr_dataset.py --input <your_dir>"
        )

    for csv_file in csv_files:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                lang = row.get("language", "").strip()
                if language_filter and lang != language_filter:
                    continue
                audio_path = row.get("audio_file", "").strip()
                transcript = row.get("transcript", "").strip()
                if audio_path and transcript:
                    samples.append(ASRSample(
                        audio_path=audio_path,
                        transcript=transcript,
                        language=lang,
                    ))

    logger.info(f"[ASR-Dataset] Loaded {len(samples)} samples from {data_dir}"
                + (f" (language={language_filter})" if language_filter else ""))
    return samples


# ============================================================
# Dry-Run Validation
# ============================================================
def validate_dataset(samples: List[ASRSample], max_duration_sec: float = 30.0) -> Dict:
    """Validate dataset integrity without loading any models."""
    report = {
        "total_samples": len(samples),
        "by_language": {},
        "missing_files": [],
        "too_long_files": [],
        "empty_transcripts": [],
    }

    for s in samples:
        lang = s.language
        report["by_language"][lang] = report["by_language"].get(lang, 0) + 1

        if not Path(s.audio_path).exists():
            report["missing_files"].append(s.audio_path)
        if not s.transcript.strip():
            report["empty_transcripts"].append(s.audio_path)

    report["valid_samples"] = (
        report["total_samples"]
        - len(report["missing_files"])
        - len(report["empty_transcripts"])
    )
    return report


# ============================================================
# HuggingFace Dataset Builder
# ============================================================
def build_hf_dataset(samples: List[ASRSample], processor, device: str):
    """Convert sample list to a HuggingFace Dataset with audio features."""
    try:
        import datasets
        import torch
        from datasets import Dataset, Audio
    except ImportError:
        raise ImportError(
            "Install HuggingFace datasets:\n"
            "  pip install datasets>=2.14.0 soundfile librosa"
        )

    data_dict = {
        "audio": [s.audio_path for s in samples],
        "sentence": [s.transcript for s in samples],
        "language": [s.language for s in samples],
    }
    dataset = Dataset.from_dict(data_dict)
    dataset = dataset.cast_column("audio", datasets.Audio(sampling_rate=16000))

    def preprocess(batch):
        audio = batch["audio"]
        inputs = processor(
            audio["array"],
            sampling_rate=audio["sampling_rate"],
            return_tensors="pt",
        )
        labels = processor.tokenizer(batch["sentence"]).input_ids
        batch["input_features"] = inputs.input_features[0]
        batch["labels"] = labels
        return batch

    dataset = dataset.map(preprocess, remove_columns=["audio", "language"])
    return dataset


# ============================================================
# Training
# ============================================================
def run_training(config: Dict, device: str, args: argparse.Namespace):
    """Run Whisper fine-tuning with HuggingFace Trainer."""
    try:
        import torch
        from transformers import (
            WhisperProcessor,
            WhisperForConditionalGeneration,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
        )
        from transformers import WhisperTokenizer, WhisperFeatureExtractor
        import evaluate
    except ImportError as e:
        raise ImportError(
            f"Missing dependency: {e}\n"
            f"Install with:\n"
            f"  pip install transformers>=4.36.0 evaluate jiwer accelerate soundfile librosa"
        )

    asr_cfg = config["asr"]
    base_model = asr_cfg["base_model"]
    output_dir = asr_cfg["output_dir"]
    train_data_dir = asr_cfg["train_data"]
    val_data_dir = asr_cfg["validation_data"]
    num_epochs = args.epochs or asr_cfg["num_train_epochs"]

    logger.info(f"[ASR-Train] Base model: {base_model}")
    logger.info(f"[ASR-Train] Output dir: {output_dir}")
    logger.info(f"[ASR-Train] Device: {device}")

    # Load processor and model
    logger.info("[ASR-Train] Loading Whisper processor...")
    processor = WhisperProcessor.from_pretrained(base_model)
    processor.tokenizer.set_prefix_tokens(language="ta", task="transcribe")

    logger.info("[ASR-Train] Loading Whisper model...")
    model = WhisperForConditionalGeneration.from_pretrained(base_model)
    model.config.forced_decoder_ids = None
    model.config.suppress_tokens = []

    if device != "cpu":
        model = model.to(device)

    # Load data
    train_samples = load_asr_dataset(train_data_dir, args.language)
    val_samples = load_asr_dataset(val_data_dir, args.language)

    logger.info(f"[ASR-Train] Train: {len(train_samples)} | Val: {len(val_samples)} samples")

    # Build HF datasets
    train_dataset = build_hf_dataset(train_samples, processor, device)
    val_dataset = build_hf_dataset(val_samples, processor, device)

    # WER metric
    wer_metric = evaluate.load("wer")

    def compute_metrics(pred):
        pred_ids = pred.predictions
        label_ids = pred.label_ids
        label_ids[label_ids == -100] = processor.tokenizer.pad_token_id
        pred_str = processor.batch_decode(pred_ids, skip_special_tokens=True)
        label_str = processor.batch_decode(label_ids, skip_special_tokens=True)
        wer = wer_metric.compute(predictions=pred_str, references=label_str)
        return {"wer": round(wer * 100, 2)}

    # Data collator
    from dataclasses import dataclass as dc
    import torch

    @dc
    class DataCollatorSpeechSeq2SeqWithPadding:
        processor: Any

        def __call__(self, features):
            import torch
            input_features = [{"input_features": f["input_features"]} for f in features]
            batch = self.processor.feature_extractor.pad(input_features, return_tensors="pt")
            label_features = [{"input_ids": f["labels"]} for f in features]
            labels_batch = self.processor.tokenizer.pad(label_features, return_tensors="pt")
            labels = labels_batch["input_ids"].masked_fill(
                labels_batch.attention_mask.ne(1), -100
            )
            if (labels[:, 0] == self.processor.tokenizer.bos_token_id).all().cpu().item():
                labels = labels[:, 1:]
            batch["labels"] = labels
            return batch

    data_collator = DataCollatorSpeechSeq2SeqWithPadding(processor=processor)

    # Training arguments (CPU-optimized defaults)
    fp16 = config.get("fp16", False) and device == "cuda"
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=asr_cfg["batch_size"],
        per_device_eval_batch_size=asr_cfg["eval_batch_size"],
        gradient_accumulation_steps=asr_cfg["gradient_accumulation_steps"],
        learning_rate=asr_cfg["learning_rate"],
        warmup_steps=asr_cfg["warmup_steps"],
        fp16=fp16,
        evaluation_strategy="steps",
        eval_steps=asr_cfg["eval_steps"],
        save_strategy="steps",
        save_steps=asr_cfg["save_steps"],
        logging_steps=asr_cfg["logging_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="wer",
        greater_is_better=False,
        predict_with_generate=True,
        generation_max_length=225,
        report_to="none",
        resume_from_checkpoint=args.resume or asr_cfg.get("resume_from_checkpoint"),
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
        tokenizer=processor.feature_extractor,
    )

    logger.info("[ASR-Train] 🚀 Starting Whisper fine-tuning...")
    trainer.train(resume_from_checkpoint=args.resume)

    # Save model + processor
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    processor.save_pretrained(output_dir)

    # Evaluate
    eval_results = trainer.evaluate()
    final_wer = eval_results.get("eval_wer", 0.0)
    logger.success(f"[ASR-Train] ✅ Training complete! WER: {final_wer:.2f}%")

    # Save metrics
    metrics_path = Path(output_dir) / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "final_wer": final_wer,
            "eval_results": eval_results,
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "num_epochs": num_epochs,
            "dataset_samples": len(train_samples),
        }, f, indent=2)

    # Update model registry
    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.ml_engine.model_registry import get_model_registry
        registry = get_model_registry()
        registry.mark_trained(
            "TRANSLARA-ASR-v1",
            metrics={"wer": final_wer},
            dataset_version="v1",
        )
        logger.info("[ASR-Train] Model registry updated")
    except Exception as e:
        logger.warning(f"[ASR-Train] Could not update model registry: {e}")

    return eval_results


# ============================================================
# Entry Point
# ============================================================
def main():
    args = parse_args()

    # Load config
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    device = detect_device(config.get("device", "auto"))
    asr_cfg = config["asr"]

    logger.info("=" * 60)
    logger.info("  TRANSLARA-ASR Fine-Tuning")
    logger.info(f"  Base Model: {asr_cfg['base_model']}")
    logger.info(f"  Output:     {asr_cfg['output_dir']}")
    logger.info(f"  Device:     {device}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[ASR-Train] DRY RUN — validating config and data only")
        try:
            train_samples = load_asr_dataset(asr_cfg["train_data"], args.language)
            val_samples = load_asr_dataset(asr_cfg["validation_data"], args.language)
            train_report = validate_dataset(train_samples)
            val_report = validate_dataset(val_samples)
            logger.info(f"[ASR-Train] Train dataset: {json.dumps(train_report, indent=2)}")
            logger.info(f"[ASR-Train] Val dataset:   {json.dumps(val_report, indent=2)}")
            if train_report["missing_files"]:
                logger.warning(f"[ASR-Train] {len(train_report['missing_files'])} missing audio files!")
            logger.success("[ASR-Train] Dry run complete — ready to train")
        except FileNotFoundError as e:
            logger.error(f"[ASR-Train] Data not found: {e}")
        return

    run_training(config, device, args)


if __name__ == "__main__":
    main()
