"""
TRANSLARA-ASR Evaluation Script
Evaluates the trained ASR model on the test set using Word Error Rate (WER).

Usage:
    python evaluation/evaluate_asr.py --model TRANSLARA-ASR-v1 --split test
    python evaluation/evaluate_asr.py --model TRANSLARA-ASR-v1 --language ta
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path
from typing import Dict, List

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


def parse_args():
    p = argparse.ArgumentParser(description="Evaluate TRANSLARA-ASR")
    p.add_argument("--model", type=str, default="TRANSLARA-ASR-v1")
    p.add_argument("--split", type=str, default="test", choices=["train", "validation", "test"])
    p.add_argument("--language", type=str, default=None)
    p.add_argument("--output-dir", type=str, default="evaluation/reports")
    p.add_argument("--max-samples", type=int, default=None)
    return p.parse_args()


def load_asr_samples(split: str, language_filter=None) -> List[Dict]:
    data_dir = ROOT / "data/asr" / split
    samples = []
    for csv_file in sorted(data_dir.glob("*.csv")):
        with open(csv_file, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                lang = row.get("language", "").strip()
                if language_filter and lang != language_filter:
                    continue
                samples.append({
                    "audio_path": row.get("audio_file", "").strip(),
                    "reference": row.get("transcript", "").strip(),
                    "language": lang,
                })
    return samples


def calculate_wer(reference: str, hypothesis: str) -> float:
    r, h = reference.split(), hypothesis.split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]
    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j
    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i-1] == h[j-1]:
                d[i][j] = d[i-1][j-1]
            else:
                d[i][j] = 1 + min(d[i-1][j], d[i][j-1], d[i-1][j-1])
    return round(d[len(r)][len(h)] / max(len(r), 1) * 100, 2)


def run_evaluation(args) -> Dict:
    from backend.ml_engine.model_registry import get_model_registry
    registry = get_model_registry()
    info = registry.get_model_info(args.model)

    if not info:
        print(f"❌ Model '{args.model}' not registered")
        return {}

    if info.status != "READY":
        print(f"⚠️  Model is NOT trained yet (status={info.status})")
        print(f"   Run: python -m training.train_asr --config config/training.yaml")
        return {"model": args.model, "status": info.status}

    model_path = Path(info.output_dir)
    print(f"Loading ASR model from {model_path}...")

    try:
        from transformers import WhisperProcessor, WhisperForConditionalGeneration
        import torch
        processor = WhisperProcessor.from_pretrained(str(model_path))
        model = WhisperForConditionalGeneration.from_pretrained(str(model_path))
        model.eval()
    except Exception as e:
        print(f"❌ Failed to load model: {e}")
        return {"model": args.model, "error": str(e)}

    samples = load_asr_samples(args.split, args.language)
    if args.max_samples:
        samples = samples[:args.max_samples]

    if not samples:
        print(f"⚠️  No test data in data/asr/{args.split}/")
        return {}

    print(f"📊 Evaluating {len(samples)} samples...")
    wer_scores = []
    results_rows = []

    for s in samples:
        audio_path = Path(s["audio_path"])
        if not audio_path.exists():
            continue

        try:
            import soundfile as sf
            import numpy as np
            audio_array, sr = sf.read(str(audio_path))
            if sr != 16000:
                from scipy.signal import resample
                audio_array = resample(audio_array, int(len(audio_array) * 16000 / sr))

            inputs = processor(audio_array, sampling_rate=16000, return_tensors="pt")
            with torch.no_grad():
                pred_ids = model.generate(inputs.input_features)
            prediction = processor.batch_decode(pred_ids, skip_special_tokens=True)[0]

            wer = calculate_wer(s["reference"], prediction)
            wer_scores.append(wer)
            results_rows.append({
                "audio": str(audio_path),
                "language": s["language"],
                "reference": s["reference"],
                "prediction": prediction,
                "wer": wer,
            })
        except Exception as e:
            print(f"  ⚠️  Skipping {audio_path.name}: {e}")

    mean_wer = round(sum(wer_scores) / max(len(wer_scores), 1), 2)
    metrics = {
        "model": args.model,
        "split": args.split,
        "evaluated": len(wer_scores),
        "mean_wer": mean_wer,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }

    out_dir = ROOT / args.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = out_dir / f"{args.model}_{args.split}_{time.strftime('%Y%m%d_%H%M%S')}.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump({"metrics": metrics, "samples": results_rows[:50]}, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 50)
    print(f"  TRANSLARA-ASR Evaluation Report")
    print(f"  Model:    {args.model}")
    print(f"  Split:    {args.split}")
    print(f"  Samples:  {len(wer_scores)}")
    print(f"  Mean WER: {mean_wer:.2f}%")
    print(f"  Report:   {report_path}")
    print("=" * 50)

    return metrics


def main():
    args = parse_args()
    run_evaluation(args)


if __name__ == "__main__":
    main()
