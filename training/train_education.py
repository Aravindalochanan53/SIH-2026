"""
TRANSLARA-EDU Fine-Tuning Script
Fine-tunes a small instruction-tuned LLM (Qwen2.5) on educational Q&A data
for primary school teaching in Indian languages (Grades 1–3).

Uses PEFT/LoRA for memory-efficient training on CPU/GPU.

Usage:
    python -m training.train_education --config config/training.yaml
    python -m training.train_education --config config/training.yaml --dry-run
    python -m training.train_education --config config/training.yaml --language ta

Dataset format (JSONL):
    {
      "grade": 1,
      "subject": "Mathematics",
      "topic": "Numbers 1-10",
      "language": "ta",
      "instruction": "Explain the number 5 to a Grade 1 student in Tamil",
      "response": "5 என்பது ஐந்து. உங்கள் கையில் ஐந்து விரல்கள் உள்ளன."
    }

Output: models/education/TRANSLARA-EDU-v1/
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
# Argument Parsing
# ============================================================
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="TRANSLARA-EDU Fine-Tuning")
    p.add_argument("--config", type=str, default="config/training.yaml")
    p.add_argument("--language", type=str, default=None,
                   help="Filter by language code (e.g. 'ta')")
    p.add_argument("--grade", type=int, default=None,
                   help="Filter by grade (1, 2, or 3)")
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
            logger.info(f"[EDU-Train] GPU: {torch.cuda.get_device_name(0)}")
            return "cuda"
    except ImportError:
        pass
    logger.warning("[EDU-Train] CPU mode — using Qwen2.5-0.5B with LoRA (manageable on CPU)")
    return "cpu"


# ============================================================
# Dataset
# ============================================================
def load_education_dataset(data_dir: str, language_filter: Optional[str] = None,
                            grade_filter: Optional[int] = None) -> List[Dict]:
    """
    Load educational instruction dataset from JSONL files.

    Each line:
    {
      "grade": 1,
      "subject": "Science",
      "topic": "Animals",
      "language": "ml",
      "instruction": "Name 3 farm animals in Malayalam",
      "response": "1. പശു (cow) 2. ആട് (goat) 3. കോഴി (chicken)"
    }
    """
    samples = []
    data_path = Path(data_dir)
    jsonl_files = list(data_path.glob("*.jsonl")) + list(data_path.glob("**/*.jsonl"))

    if not jsonl_files:
        raise FileNotFoundError(
            f"No JSONL files found in {data_dir}.\n\n"
            f"Expected JSONL format (one JSON per line):\n"
            f'  {{"grade": 1, "subject": "Math", "topic": "Numbers", "language": "ta", '
            f'"instruction": "Count to 5 in Tamil", "response": "ஒன்று இரண்டு மூன்று நான்கு ஐந்து"}}\n\n'
            f"Run: python scripts/prepare_education_dataset.py --demo"
        )

    for jsonl_file in jsonl_files:
        with open(jsonl_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                except json.JSONDecodeError:
                    continue
                lang = str(obj.get("language", ""))
                grade = obj.get("grade")
                if language_filter and lang != language_filter:
                    continue
                if grade_filter and grade != grade_filter:
                    continue
                instruction = obj.get("instruction", "").strip()
                response = obj.get("response", "").strip()
                if instruction and response:
                    samples.append(obj)

    logger.info(f"[EDU-Dataset] Loaded {len(samples)} samples from {data_dir}")
    return samples


def validate_education_dataset(samples: List[Dict]) -> Dict:
    by_lang = {}
    by_grade = {}
    by_subject = {}
    for s in samples:
        lang = s.get("language", "unknown")
        grade = str(s.get("grade", "unknown"))
        subject = s.get("subject", "unknown")
        by_lang[lang] = by_lang.get(lang, 0) + 1
        by_grade[grade] = by_grade.get(grade, 0) + 1
        by_subject[subject] = by_subject.get(subject, 0) + 1
    return {
        "total": len(samples),
        "by_language": by_lang,
        "by_grade": by_grade,
        "by_subject": by_subject,
    }


# ============================================================
# Prompt Formatting
# ============================================================
SYSTEM_PROMPT = (
    "You are TRANSLARA-EDU, an AI teaching assistant for primary school students "
    "in Indian languages. You explain concepts clearly and simply for Grades 1-3. "
    "Always respond in the requested language. Never echo back the question as the answer."
)


def format_prompt(sample: Dict, tokenizer) -> str:
    instruction = sample["instruction"]
    response = sample["response"]
    grade = sample.get("grade", "")
    subject = sample.get("subject", "")
    lang = sample.get("language", "")
    topic = sample.get("topic", "")

    user_msg = f"[Grade {grade} | {subject} | {topic} | Language: {lang}]\n{instruction}"

    # Format as ChatML (Qwen2.5 format)
    chat = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_msg},
        {"role": "assistant", "content": response},
    ]
    return tokenizer.apply_chat_template(chat, tokenize=False, add_generation_prompt=False)


# ============================================================
# Training
# ============================================================
def run_training(config: Dict, device: str, args: argparse.Namespace):
    try:
        import torch
        from transformers import (
            AutoTokenizer,
            AutoModelForCausalLM,
            TrainingArguments,
            Trainer,
            DataCollatorForLanguageModeling,
        )
        from peft import LoraConfig, get_peft_model, TaskType
        from datasets import Dataset
    except ImportError as e:
        raise ImportError(
            f"Missing: {e}\n"
            f"pip install transformers>=4.40.0 peft>=0.10.0 datasets accelerate"
        )

    cfg = config["education"]
    base_model = cfg["base_model"]
    output_dir = cfg["output_dir"]
    num_epochs = args.epochs or cfg["num_train_epochs"]
    max_length = cfg["max_length"]
    use_lora = cfg.get("use_lora", True)

    logger.info(f"[EDU-Train] Base model:  {base_model}")
    logger.info(f"[EDU-Train] Output:      {output_dir}")
    logger.info(f"[EDU-Train] Device:      {device}")
    logger.info(f"[EDU-Train] LoRA:        {use_lora}")

    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(base_model, trust_remote_code=True)
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    # Load model
    model = AutoModelForCausalLM.from_pretrained(
        base_model,
        trust_remote_code=True,
        torch_dtype=torch.float32 if device == "cpu" else torch.float16,
    )

    # Apply LoRA for parameter-efficient fine-tuning
    if use_lora:
        lora_config = LoraConfig(
            task_type=TaskType.CAUSAL_LM,
            r=cfg.get("lora_r", 16),
            lora_alpha=cfg.get("lora_alpha", 32),
            lora_dropout=cfg.get("lora_dropout", 0.1),
            target_modules=cfg.get("lora_target_modules", ["q_proj", "v_proj"]),
            bias="none",
        )
        model = get_peft_model(model, lora_config)
        model.print_trainable_parameters()

    if device != "cpu":
        model = model.to(device)

    # Load datasets
    train_samples = load_education_dataset(cfg["train_data"], args.language, args.grade)
    # For education, use 10% of train data as validation if no separate val set
    split_idx = max(1, int(len(train_samples) * 0.9))
    val_samples = train_samples[split_idx:]
    train_samples = train_samples[:split_idx]

    logger.info(f"[EDU-Train] Train: {len(train_samples)} | Val: {len(val_samples)}")

    # Build tokenized datasets
    def tokenize_sample(batch):
        texts = [format_prompt(s, tokenizer) for s in batch["samples"]]
        tokenized = tokenizer(
            texts,
            max_length=max_length,
            truncation=True,
            padding="max_length",
            return_tensors=None,
        )
        tokenized["labels"] = tokenized["input_ids"].copy()
        return tokenized

    # Flatten into HF Dataset
    train_ds = Dataset.from_dict({"samples": train_samples})
    val_ds = Dataset.from_dict({"samples": val_samples})

    train_ds = train_ds.map(
        lambda batch: tokenize_sample(batch),
        batched=True,
        batch_size=32,
        remove_columns=["samples"],
    )
    val_ds = val_ds.map(
        lambda batch: tokenize_sample(batch),
        batched=True,
        batch_size=32,
        remove_columns=["samples"],
    )

    data_collator = DataCollatorForLanguageModeling(tokenizer=tokenizer, mlm=False)

    fp16 = config.get("fp16", False) and device == "cuda"
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=num_epochs,
        per_device_train_batch_size=cfg["batch_size"],
        per_device_eval_batch_size=cfg["batch_size"],
        gradient_accumulation_steps=cfg["gradient_accumulation_steps"],
        learning_rate=cfg["learning_rate"],
        fp16=fp16,
        evaluation_strategy="steps",
        eval_steps=cfg.get("save_steps", 200),
        save_strategy="steps",
        save_steps=cfg.get("save_steps", 200),
        logging_steps=cfg.get("logging_steps", 20),
        load_best_model_at_end=True,
        report_to="none",
        remove_unused_columns=False,
        resume_from_checkpoint=args.resume,
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=val_ds,
        tokenizer=tokenizer,
        data_collator=data_collator,
    )

    logger.info("[EDU-Train] 🚀 Starting Qwen2.5-EDU fine-tuning with LoRA...")
    trainer.train(resume_from_checkpoint=args.resume)

    # Save — merge LoRA weights before saving for production
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    if use_lora:
        logger.info("[EDU-Train] Merging LoRA weights...")
        model = model.merge_and_unload()
    trainer.save_model(output_dir)
    tokenizer.save_pretrained(output_dir)

    eval_results = trainer.evaluate()
    logger.success(f"[EDU-Train] ✅ Education model saved to {output_dir}")
    logger.info(f"[EDU-Train] Eval loss: {eval_results.get('eval_loss', 'N/A'):.4f}")

    with open(Path(output_dir) / "training_metrics.json", "w") as mf:
        json.dump({
            "base_model": base_model,
            "training_date": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "eval_results": eval_results,
            "train_samples": len(train_samples),
            "use_lora": use_lora,
        }, mf, indent=2)

    try:
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from backend.ml_engine.model_registry import get_model_registry
        get_model_registry().mark_trained(
            "TRANSLARA-EDU-v1",
            metrics={"eval_loss": eval_results.get("eval_loss", 0)},
        )
    except Exception as e:
        logger.warning(f"[EDU-Train] Registry update: {e}")

    return eval_results


# ============================================================
# Entry Point
# ============================================================
def main():
    args = parse_args()
    with open(args.config, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)

    device = detect_device(config.get("device", "auto"))
    cfg = config["education"]

    logger.info("=" * 60)
    logger.info("  TRANSLARA-EDU Fine-Tuning (Qwen2.5 + LoRA)")
    logger.info(f"  Base Model: {cfg['base_model']}")
    logger.info(f"  Device:     {device}")
    logger.info("=" * 60)

    if args.dry_run:
        logger.info("[EDU-Train] DRY RUN")
        try:
            samples = load_education_dataset(cfg["train_data"], args.language, args.grade)
            report = validate_education_dataset(samples)
            logger.info(f"[EDU-Train] Report:\n{json.dumps(report, indent=2)}")
        except FileNotFoundError as e:
            logger.error(str(e))
        return

    run_training(config, device, args)


if __name__ == "__main__":
    main()
