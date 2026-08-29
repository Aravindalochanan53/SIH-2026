"""
TRANSLARA-NER Fine-Tuning Script
Fine-tunes XLM-RoBERTa on Indian language Named Entity Recognition (IOB2 format).

Usage:
    python -m training.train_ner --config config/training.yaml
    python -m training.train_ner --config config/training.yaml --dry-run
    python -m training.train_ner --config config/training.yaml --language ta

Base model: xlm-roberta-base (multilingual, fully open)
Output:     models/ner/TRANSLARA-NER-v1/

Dataset format (JSONL, one sentence per line):
    {"tokens": ["வணக்கம்", "ராமன்", "பள்ளி", "சென்றான்"], "ner_tags": ["O", "B-PERSON", "B-SCHOOL", "O"], "language": "ta"}
    {"tokens": ["Hello", "Raman", "went", "to", "school"], "ner_tags": ["O", "B-PERSON", "O", "O", "B-SCHOOL"], "language": "en"}
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml
from loguru import logger


# ============================================================
# IOB2 NER Label Set (matches config/training.yaml)
# ============================================================
NER_LABELS = [
    "O", "B-PERSON", "I-PERSON", "B-LOCATION", "I-LOCATION",
    "B-VILLAGE", "I-VILLAGE", "B-SCHOOL", "I-SCHOOL",
    "B-ORGANIZATION", "I-ORGANIZATION", "B-NUMBER", "I-NUMBER",
    "B-DATE", "I-DATE", "B-TIME", "I-TIME",
    "B-CLASS", "I-CLASS", "B-SUBJECT", "I-SUBJECT",
]
LABEL2ID = {l: i for i, l in enumerate(NER_LABELS)}
ID2LABEL = {i: l for i, l in enumerate(NER_LABELS)}


# ============================================================
# Argument Parsing
# ============================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TRANSLARA-NER Fine-Tuning")
    p.add_argument("--config", type=str, default="config/training.yaml")
    p.add_argument("--language", type=str, default=None)
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
def load_ner_dataset(data_dir: str, language_filter: Optional[str] = None) -> List[Dict]:
    """
    Load IOB2 NER dataset from JSONL files.

    Each line is a JSON object:
        {
          "tokens": ["word1", "word2", ...],
          "ner_tags": ["O", "B-PERSON", ...],
          "language": "ta"
        }

    Place files in:
        data/ner/train/
        data/ner/validation/
        data/ner/test/
    """
    samples = []
    data_path = Path(data_dir)
    jsonl_files = list(data_path.glob("*.jsonl")) + list(data_path.glob("**/*.jsonl"))

    if not jsonl_files:
        raise FileNotFoundError(
            f"No JSONL files found in {data_dir}.\n\n"
            f"Expected JSONL format (one JSON per line):\n"
            f'  {{"tokens": ["ராமன்", "பள்ளி", "சென்றான்"], "ner_tags": ["B-PERSON", "B-SCHOOL", "O"], "language": "ta"}}\n\n'
            f"Run the sample generator:\n"
            f"  python scripts/prepare_ner_dataset.py --demo"
        )

    for jsonl_file in jsonl_files:
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                lang = obj.get("language", "")
                if language_filter and lang != language_filter:
                    continue
                tokens = obj.get("tokens", [])
                tags = obj.get("ner_tags", [])
                if len(tokens) != len(tags):
                    logger.warning(f"[NER-Dataset] Token/tag length mismatch, skipping: {obj}")
                    continue
                # Validate tags
                valid = all(t in LABEL2ID for t in tags)
                if not valid:
                    unknown = [t for t in tags if t not in LABEL2ID]
                    logger.warning(f"[NER-Dataset] Unknown tags {unknown}, skipping")
                    continue
                samples.append({"tokens": tokens, "ner_tags": tags, "language": lang})

    logger.info(f"[NER-Dataset] Loaded {len(samples)} sentences from {data_dir}")
    return samples


def validate_ner_dataset(samples: List[Dict]) -> Dict:
    by_lang = {}
    entity_counts = {}
    for s in samples:
        lang = s.get("language", "unknown")
        by_lang[lang] = by_lang.get(lang, 0) + 1
        for tag in s["ner_tags"]:
            if tag.startswith("B-"):
                entity = tag[2:]
                entity_counts[entity] = entity_counts.get(entity, 0) + 1
    return {"total_sentences": len(samples), "by_language": by_lang, "entity_counts": entity_counts}


# ============================================================
# HuggingFace Dataset Builder
# ============================================================
def build_hf_dataset(samples: List[Dict], tokenizer, max_length: int):
    try:
        from datasets import Dataset
    except ImportError:
        raise ImportError("pip install datasets>=2.14.0")

    def tokenize_and_align(batch):
        tokenized = tokenizer(
            batch["tokens"],
            is_split_into_words=True,
            max_length=max_length,
            truncation=True,
            padding="max_length",
        )
        all_labels = []
        for i, label_seq in enumerate(batch["ner_tags"]):
            word_ids = tokenized.word_ids(batch_index=i)
            label_ids = []
            prev_word_id = None
            for word_id in word_ids:
                if word_id is None:
                    label_ids.append(-100)
                elif word_id != prev_word_id:
                    label_ids.append(LABEL2ID[label_seq[word_id]])
                else:
                    # Sub-word tokens get I- label or -100
                    tag = label_seq[word_id]
                    if tag.startswith("B-"):
                        label_ids.append(LABEL2ID["I-" + tag[2:]])
                    else:
                        label_ids.append(LABEL2ID[tag])
                prev_word_id = word_id
            all_labels.append(label_ids)
        tokenized["labels"] = all_labels
        return tokenized

    raw = {
        "tokens": [s["tokens"] for s in samples],
        "ner_tags": [s["ner_tags"] for s in samples],
    }
    ds = Dataset.from_dict(raw)
    ds = ds.map(tokenize_and_align, batched=True, remove_columns=["tokens", "ner_tags"])
    return ds


# ============================================================
# Training
# ============================================================
def run_training(config: Dict, device: str, args: argparse.Namespace):
    try:
        from transformers import (
            AutoTokenizer,
            AutoModelForTokenClassification,
            TrainingArguments,
            Trainer,
            DataCollatorForTokenClassification,
        )
        import evaluate
        import numpy as np
    except ImportError as e:
        raise ImportError(f"Missing: {e}\npip install transformers>=4.36.0 evaluate seqeval")

    cfg = config["ner"]
    base_model = cfg["base_model"]
    output_dir = cfg["output_dir"]
    num_epochs = args.epochs or cfg["num_train_epochs"]
    max_length = cfg["max_length"]

    logger.info(f"[NER-Train] Base model: {base_model}")
    logger.info(f"[NER-Train] Output:     {output_dir}")
    logger.info(f"[NER-Train] Device:     {device}")
    logger.info(f"[NER-Train] Labels:     {len(NER_LABELS)}")

    tokenizer = AutoTokenizer.from_pretrained(base_model)
    model = AutoModelForTokenClassification.from_pretrained(
        base_model,
        num_labels=len(NER_LABELS),
        id2label=ID2LABEL,
        label2id=LABEL2ID,
    )
    if device != "cpu":
        model = model.to(device)

    train_samples = load_ner_dataset(cfg["train_data"], args.language)
    val_samples = load_ner_dataset(cfg["validation_data"], args.language)

    train_ds = build_hf_dataset(train_samples, tokenizer, max_length)
    val_ds = build_hf_dataset(val_samples, tokenizer, max_length)

    data_collator = DataCollatorForTokenClassification(tokenizer)
    seqeval = evaluate.load("seqeval")

    def compute_metrics(p):
        predictions, labels = p
        predictions = predictions.argmax(-1)
        true_labels = [[ID2LABEL[l] for l in label if l != -100] for label in labels]
        true_preds = [
            [ID2LABEL[pred] for pred, lab in zip(prediction, label) if lab != -100]
            for prediction, label in zip(predictions, labels)
        ]
        result = seqeval.compute(predictions=true_preds, references=true_labels)
        return {
            "precision": round(result["overall_precision"] * 100, 2),
            "recall": round(result["overall_recall"] * 100, 2),
            "f1": round(result["overall_f1"] * 100, 2),
        }

    fp16 = config.get("fp16", False) and device == "cuda"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=cfg["batch_size"],
        per_device_eval_batch_size=cfg["eval_batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        fp16=fp16,
        evaluation_strategy="steps",
        eval_steps=cfg["eval_steps"],
        save_strategy="steps",
        save_steps=cfg["save_steps"],
        logging_steps=cfg["logging_steps"],
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        greater_is_better=True,
        report_to="none",
        resume_from_checkpoint=args.resume or cfg.get("resume_from_checkpoint"),
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )

    logger.info("[NER-Train] 🚀 Starting XLM-RoBERTa NER fine-tuning...")
    trainer.train(resume_from_checkpoint=args.resume)

    Path(output_dir).mkdir(parents=True, exist_ok=True)
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    eval_results = trainer.evaluate()
    f1 = eval_results.get("eval_f1", 0.0)
    logger.success(f"[NER-Train] ✅ Done! F1: {f1:.2f}%")

    with open(Path(output_dir) / "training_metrics.json", "w") as mf:
        json.dump({
            "final_f1": f1, "eval_results": eval_results,
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "labels": NER_LABELS,
        }, mf, indent=2)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.ml_engine.model_registry import get_model_registry
        get_model_registry().mark_trained("TRANSLARA-NER-v1", metrics={"f1": f1})
    except Exception as e:
        logger.warning(f"[NER-Train] Registry update failed: {e}")

    return eval_results


def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    device = detect_device(config.get("device", "auto"))

    logger.info("=" * 60)
    logger.info("  TRANSLARA-NER Fine-Tuning (XLM-RoBERTa)")
    logger.info(f"  Base model: {config['ner']['base_model']}")
    logger.info(f"  Device:     {device}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[NER-Train] DRY RUN")
        try:
            samples = load_ner_dataset(config["ner"]["train_data"], args.language)
            report = validate_ner_dataset(samples)
            logger.info(f"[NER-Train] Report:\n{json.dumps(report, indent=2)}")
        except FileNotFoundError as e:
            logger.error(str(e))
        return

    run_training(config, device, args)


if __name__ == "__main__":
    main()
