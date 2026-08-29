"""
TRANSLARA-NMT Evaluation Script
Evaluates the trained translation model on the test set.

Usage:
    python evaluation/evaluate_translation.py --model TRANSLARA-NMT-v1 --split test
    python evaluation/evaluate_translation.py --model TRANSLARA-NMT-v1 --src ta --tgt ml
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate TRANSLARA-NMT")
    p.add_argument("--model", type=str, default="TRANSLARA-NMT-v1")
    p.add_argument("--split", type=str, default="test", choices=["train", "validation", "test"])
    p.add_argument("--src", type=str, default=None)
    p.add_argument("--tgt", type=str, default=None)
    p.add_argument("--output-dir", type=str, default="evaluation/reports")
    p.add_argument("--max-samples", type=int, default=None)
    return p.parse_args()


NLLB_LANG_MAP = {
    "ta": "tam_Taml", "ml": "mal_Mlym", "te": "tel_Telu",
    "kn": "kan_Knda", "hi": "hin_Deva", "en": "eng_Latn",
}


def load_test_pairs(split: str, src_filter=None, tgt_filter=None) -> List[Dict]:
    data_dir = ROOT / "data/translation" / split
    pairs = []
    for csv_file in sorted(data_dir.glob("*.csv")):
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                src = row.get("src_lang", "").strip()
                tgt = row.get("tgt_lang", "").strip()
                if src_filter and src != src_filter:
                    continue
                if tgt_filter and tgt != tgt_filter:
                    continue
                pairs.append({
                    "src_lang": src, "tgt_lang": tgt,
                    "src_text": row.get("src_text", "").strip(),
                    "tgt_text": row.get("tgt_text", "").strip(),
                })
    return pairs


def run_evaluation(args) -> Dict:
    from backend.ml_engine.model_registry import get_model_registry
    registry = get_model_registry()
    info = registry.get_model_info(args.model)

    if not info:
        print(f"❌ Model '{args.model}' not found in registry")
        return {}

    model_path = Path(info.output_dir)

    if info.status != "READY":
        print(f"⚠️  Model '{args.model}' is NOT trained yet (status={info.status})")
        print(f"   Run: python -m training.train_translation --config config/training.yaml")
        return {"model": args.model, "status": info.status, "error": "not_trained"}

    print(f"✅ Loading model from {model_path}...")
    try:
        from transformers import AutoTokenizer, AutoModelForSeq2SeqLM
        tokenizer = AutoTokenizer.from_pretrained(str(model_path))
        model = AutoModelForSeq2SeqLM.from_pretrained(str(model_path))
        model.eval()
    except Exception as e:
        return {"model": args.model, "error": str(e)}

    pairs = load_test_pairs(args.split, args.src, args.tgt)
    if args.max_samples:
        pairs = pairs[:args.max_samples]

    if not pairs:
        print(f"⚠️  No test pairs found in data/translation/{args.split}/")
        return {}

    print(f"📊 Evaluating {len(pairs)} pairs from '{args.split}' split...")

    try:
        import evaluate
        bleu_metric = evaluate.load("sacrebleu")
        chrf_metric = evaluate.load("chrf")
    except ImportError:
        bleu_metric = None
        chrf_metric = None
        print("⚠️  Install 'evaluate' for BLEU/chrF metrics: pip install evaluate sacrebleu")

    predictions = []
    references = []
    source_echo_count = 0
    results_rows = []

    for pair in pairs:
        src_code = NLLB_LANG_MAP.get(pair["src_lang"])
        tgt_code = NLLB_LANG_MAP.get(pair["tgt_lang"])
        if not src_code or not tgt_code:
            continue

        tokenizer.src_lang = src_code
        inputs = tokenizer(pair["src_text"], return_tensors="pt", max_length=256, truncation=True)

        import torch
        with torch.no_grad():
            forced_bos = tokenizer.lang_code_to_id.get(tgt_code)
            outputs = model.generate(
                **inputs,
                forced_bos_token_id=forced_bos,
                max_new_tokens=256,
            )
        pred = tokenizer.batch_decode(outputs, skip_special_tokens=True)[0]

        # Check source echo
        if pred.strip() == pair["src_text"].strip():
            source_echo_count += 1

        predictions.append(pred)
        references.append([pair["tgt_text"]])
        results_rows.append({
            "src_lang": pair["src_lang"],
            "tgt_lang": pair["tgt_lang"],
            "source": pair["src_text"],
            "reference": pair["tgt_text"],
            "prediction": pred,
            "is_echo": pred.strip() == pair["src_text"].strip(),
        })

    metrics = {
        "model": args.model,
        "split": args.split,
        "total_pairs": len(pairs),
        "evaluated": len(predictions),
        "source_echo_count": source_echo_count,
        "source_echo_rate": round(source_echo_count / max(len(predictions), 1) * 100, 2),
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    if bleu_metric and predictions:
        bleu = bleu_metric.compute(predictions=predictions, references=references)
        metrics["bleu"] = round(bleu["score"], 2)

    if chrf_metric and predictions:
        chrf = chrf_metric.compute(predictions=predictions, references=references)
        metrics["chrf"] = round(chrf["score"], 2)

    # Save report
    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{args.model}_{args.split}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "samples": results_rows[:50]}, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n" + "=" * 50)
    print(f"  TRANSLARA-NMT Evaluation Report")
    print(f"  Model:   {args.model}")
    print(f"  Split:   {args.split}")
    print(f"  Pairs:   {len(predictions)}")
    if "bleu" in metrics:
        print(f"  BLEU:    {metrics['bleu']:.2f}")
    if "chrf" in metrics:
        print(f"  chrF:    {metrics['chrf']:.2f}")
    print(f"  Echo rate: {metrics['source_echo_rate']:.1f}%")
    print(f"  Report:  {report_path}")
    print("=" * 50)

    # Update registry
    try:
        from backend.ml_engine.model_registry import get_model_registry
        get_model_registry().update_status(args.model, "READY", metrics)
    except Exception:
        pass

    return metrics


def main():
    args = parse_args()
    run_evaluation(args)


if __name__ == "__main__":
    main()
