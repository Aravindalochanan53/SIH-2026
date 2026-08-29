"""
TRANSLARA-NMT Fine-Tuning Script
Fine-tunes facebook/nllb-200-distilled-600M on custom Indian language parallel corpus.

Usage:
    python -m training.train_translation --config config/training.yaml
    python -m training.train_translation --config config/training.yaml --dry-run
    python -m training.train_translation --config config/training.yaml --src ta --tgt ml

Base model: facebook/nllb-200-distilled-600M (fully open, no HF token needed)
Output:     models/translation/TRANSLARA-NMT-v1/
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
from typing import Any, Dict, List, Optional, Tuple

import yaml
from loguru import logger


# ============================================================
# NLLB language code mapping for our supported languages
# ============================================================
NLLB_LANG_MAP = {
    "ta":  "tam_Taml",
    "ml":  "mal_Mlym",
    "te":  "tel_Telu",
    "kn":  "kan_Knda",
    "hi":  "hin_Deva",
    "en":  "eng_Latn",
    "sat": "sat_Olck",  # Santali (Ol Chiki script) — limited NLLB support
    "hoc": None,        # Ho — not in NLLB, needs custom vocab
    "unr": None,        # Mundari — not in NLLB, needs custom vocab
}


def get_nllb_code(lang: str) -> Optional[str]:
    return NLLB_LANG_MAP.get(lang)


# ============================================================
# Argument Parsing
# ============================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TRANSLARA-NMT Fine-Tuning (NLLB-200)")
    p.add_argument("--config", type=str, default="config/training.yaml")
    p.add_argument("--src", type=str, default=None, help="Filter: source language code (e.g. 'ta')")
    p.add_argument("--tgt", type=str, default=None, help="Filter: target language code (e.g. 'ml')")
    p.add_argument("--dry-run", action="store_true", help="Validate data without training")
    p.add_argument("--resume", type=str, default=None)
    p.add_argument("--epochs", type=int, default=None)
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
            logger.info(f"[NMT-Train] CUDA: {torch.cuda.get_device_name(0)}")
            return "cuda"
        if hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
            return "mps"
    except ImportError:
        pass
    logger.warning("[NMT-Train] CPU mode — training will be slow. Consider a GPU machine.")
    return "cpu"


# ============================================================
# Dataset
# ============================================================
@dataclass
class TranslationPair:
    src_lang: str
    tgt_lang: str
    src_text: str
    tgt_text: str


def load_translation_dataset(
    data_dir: str,
    src_filter: Optional[str] = None,
    tgt_filter: Optional[str] = None,
) -> List[TranslationPair]:
    """
    Load parallel translation dataset from CSV files.

    Expected CSV format (comma-separated, UTF-8):
        src_lang,tgt_lang,src_text,tgt_text
        ta,ml,வணக்கம்,നമസ്കാരം
        en,ta,Hello students,வணக்கம் மாணவர்களே
        hi,kn,नमस्ते,ನಮಸ್ಕಾರ

    Place CSVs in:
        data/translation/train/    (training pairs)
        data/translation/validation/
        data/translation/test/
    """
    pairs: List[TranslationPair] = []
    data_path = Path(data_dir)
    csv_files = list(data_path.glob("*.csv")) + list(data_path.glob("**/*.csv"))

    if not csv_files:
        raise FileNotFoundError(
            f"No CSV files found in {data_dir}.\n\n"
            f"Expected format: src_lang,tgt_lang,src_text,tgt_text\n"
            f"Example row:     ta,ml,வணக்கம்,നമസ്കാരം\n\n"
            f"Place your parallel corpus CSV files in:\n"
            f"  {data_dir}/my_data.csv\n\n"
            f"Or run the sample data generator:\n"
            f"  python scripts/prepare_translation_dataset.py --demo"
        )

    for csv_file in csv_files:
        with open(csv_file, newline="", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                src = row.get("src_lang", "").strip()
                tgt = row.get("tgt_lang", "").strip()
                src_text = row.get("src_text", "").strip()
                tgt_text = row.get("tgt_text", "").strip()

                if src_filter and src != src_filter:
                    continue
                if tgt_filter and tgt != tgt_filter:
                    continue
                if src_text and tgt_text and src_text != tgt_text:  # Reject source echo
                    pairs.append(TranslationPair(src, tgt, src_text, tgt_text))

    by_pair: Dict[str, int] = {}
    for p in pairs:
        key = f"{p.src_lang}->{p.tgt_lang}"
        by_pair[key] = by_pair.get(key, 0) + 1

    logger.info(f"[NMT-Dataset] Loaded {len(pairs)} pairs from {data_dir}")
    for pair_key, count in sorted(by_pair.items()):
        logger.info(f"  {pair_key}: {count} samples")

    return pairs


def validate_translation_dataset(pairs: List[TranslationPair]) -> Dict:
    """Check for echo (src==tgt), empty strings, and unsupported langs."""
    echo_pairs = [p for p in pairs if p.src_text.strip() == p.tgt_text.strip()]
    empty_pairs = [p for p in pairs if not p.src_text or not p.tgt_text]
    unsupported = [p for p in pairs if get_nllb_code(p.src_lang) is None or get_nllb_code(p.tgt_lang) is None]

    return {
        "total": len(pairs),
        "valid": len(pairs) - len(echo_pairs) - len(empty_pairs),
        "echo_pairs": len(echo_pairs),
        "empty_pairs": len(empty_pairs),
        "unsupported_lang_pairs": len(unsupported),
        "unsupported_langs": list({p.src_lang for p in unsupported} | {p.tgt_lang for p in unsupported}),
    }


# ============================================================
# HuggingFace Dataset Builder
# ============================================================
def build_hf_dataset(pairs: List[TranslationPair], tokenizer, max_length: int):
    try:
        from datasets import Dataset
    except ImportError:
        raise ImportError("pip install datasets>=2.14.0")

    def tokenize(batch):
        src_texts = batch["src_text"]
        tgt_texts = batch["tgt_text"]
        src_langs = batch["src_lang"]
        tgt_langs = batch["tgt_lang"]

        model_inputs = []
        labels_list = []

        for src, tgt, sl, tl in zip(src_texts, tgt_texts, src_langs, tgt_langs):
            src_code = get_nllb_code(sl)
            tgt_code = get_nllb_code(tl)
            if not src_code or not tgt_code:
                continue
            tokenizer.src_lang = src_code
            enc = tokenizer(src, max_length=max_length, truncation=True, padding="max_length")
            with tokenizer.as_target_tokenizer():
                lab = tokenizer(tgt, max_length=max_length, truncation=True, padding="max_length")
            model_inputs.append(enc)
            labels_list.append(lab["input_ids"])

        return {
            "input_ids": [m["input_ids"] for m in model_inputs],
            "attention_mask": [m["attention_mask"] for m in model_inputs],
            "labels": labels_list,
        }

    raw = {
        "src_lang": [p.src_lang for p in pairs],
        "tgt_lang": [p.tgt_lang for p in pairs],
        "src_text": [p.src_text for p in pairs],
        "tgt_text": [p.tgt_text for p in pairs],
    }
    ds = Dataset.from_dict(raw)
    ds = ds.map(tokenize, batched=True, remove_columns=["src_lang", "tgt_lang", "src_text", "tgt_text"])
    return ds


# ============================================================
# Training
# ============================================================
def run_training(config: Dict, device: str, args: argparse.Namespace):
    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForSeq2SeqLM,
            DataCollatorForSeq2Seq,
            Seq2SeqTrainer,
            Seq2SeqTrainingArguments,
        )
        import evaluate
    except ImportError as e:
        raise ImportError(
            f"Missing: {e}\n"
            f"pip install transformers>=4.36.0 evaluate sacrebleu sentencepiece accelerate"
        )

    cfg = config["translation"]
    base_model = cfg["base_model"]
    output_dir = cfg["output_dir"]
    max_src_len = cfg["max_source_length"]
    max_tgt_len = cfg["max_target_length"]
    num_epochs = args.epochs or cfg["num_train_epochs"]

    logger.info(f"[NMT-Train] Base model:  {base_model}")
    logger.info(f"[NMT-Train] Output:      {output_dir}")
    logger.info(f"[NMT-Train] Device:      {device}")
    logger.info(f"[NMT-Train] Epochs:      {num_epochs}")

    # Load tokenizer + model
    logger.info("[NMT-Train] Loading NLLB tokenizer...")
    tokenizer = AutoTokenizer.from_pretrained(base_model)

    logger.info("[NMT-Train] Loading NLLB model...")
    model = AutoModelForSeq2SeqLM.from_pretrained(base_model)
    if device != "cpu":
        model = model.to(device)

    # Load datasets
    train_pairs = load_translation_dataset(cfg["train_data"], args.src, args.tgt)
    val_pairs = load_translation_dataset(cfg["validation_data"], args.src, args.tgt)

    logger.info(f"[NMT-Train] Train: {len(train_pairs)} | Val: {len(val_pairs)} pairs")

    train_ds = build_hf_dataset(train_pairs, tokenizer, max_src_len)
    val_ds = build_hf_dataset(val_pairs, tokenizer, max_tgt_len)

    data_collator = DataCollatorForSeq2Seq(tokenizer, model=model, padding=True)

    # BLEU metric
    bleu_metric = evaluate.load("sacrebleu")

    def compute_metrics(eval_preds):
        preds, labels = eval_preds
        if isinstance(preds, tuple):
            preds = preds[0]
        decoded_preds = tokenizer.batch_decode(preds, skip_special_tokens=True)
        labels = [[l for l in label if l != -100] for label in labels]
        decoded_labels = tokenizer.batch_decode(labels, skip_special_tokens=True)
        decoded_preds = [p.strip() for p in decoded_preds]
        decoded_labels = [[l.strip()] for l in decoded_labels]
        result = bleu_metric.compute(predictions=decoded_preds, references=decoded_labels)
        return {"bleu": round(result["score"], 2)}

    fp16 = config.get("fp16", False) and device == "cuda"
    training_args = Seq2SeqTrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=cfg["batch_size"],
        per_device_eval_batch_size=cfg["eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        warmup_ratio=cfg["warmup_ratio"],
        weight_decay=cfg["weight_decay"],
        fp16=fp16,
        evaluation_strategy="steps",
        eval_steps=cfg["eval_steps"],
        save_strategy="steps",
        save_steps=cfg["save_steps"],
        logging_steps=cfg["logging_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="bleu",
        greater_is_better=True,
        predict_with_generate=True,
        generation_max_length=max_tgt_len,
        report_to="none",
        resume_from_checkpoint=args.resume or cfg.get("resume_from_checkpoint"),
    )

    trainer = Seq2SeqTrainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("[NMT-Train] 🚀 Starting NLLB fine-tuning...")
    trainer.train(resume_from_checkpoint=args.resume)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    eval_results = trainer.evaluate()
    final_bleu = eval_results.get("eval_bleu", 0.0)
    logger.success(f"[NMT-Train] ✅ Training complete! BLEU: {final_bleu:.2f}")

    metrics_path = Path(output_dir) / "training_metrics.json"
    with open(metrics_path, "w") as f:
        json.dump({
            "final_bleu": final_bleu,
            "eval_results": eval_results,
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "num_epochs": num_epochs,
            "train_pairs": len(train_pairs),
        }, f, indent=2)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.ml_engine.model_registry import get_model_registry
        get_model_registry().mark_trained(
            "TRANSLARA-NMT-v1",
            metrics={"bleu": final_bleu},
            dataset_version="v1",
        )
    except Exception as e:
        logger.warning(f"[NMT-Train] Registry update failed: {e}")

    return eval_results


# ============================================================
# Entry Point
# ============================================================
def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    device = detect_device(config.get("device", "auto"))
    cfg = config["translation"]

    logger.info("=" * 60)
    logger.info("  TRANSLARA-NMT Fine-Tuning")
    logger.info(f"  Base Model : {cfg['base_model']}")
    logger.info(f"  Output     : {cfg['output_dir']}")
    logger.info(f"  Device     : {device}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[NMT-Train] DRY RUN — validating data only")
        try:
            pairs = load_translation_dataset(cfg["train_data"], args.src, args.tgt)
            report = validate_translation_dataset(pairs)
            logger.info(f"[NMT-Train] Validation report:\n{json.dumps(report, indent=2)}")
            if report["echo_pairs"] > 0:
                logger.warning(f"[NMT-Train] ⚠️  {report['echo_pairs']} source-echo pairs detected (will be rejected)")
            logger.success("[NMT-Train] Dry run complete")
        except FileNotFoundError as e:
            logger.error(str(e))
        return

    run_training(config, device, args)


if __name__ == "__main__":
    main()
