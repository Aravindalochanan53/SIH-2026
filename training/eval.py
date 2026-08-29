"""
Automated Evaluation Suite for TRANSLARA AI.
Runs test sets across all language pairs and generates comprehensive quality metrics.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.ai.translation.registry import get_translation_engine
from backend.ai.validators.script_validator import calculate_script_purity
from training.dataset_prep import load_dataset
from training.metrics import calculate_entity_preservation, calculate_word_overlap_bleu


async def evaluate_pair(source_lang: str, target_lang: str) -> dict:
    dataset = load_dataset(source_lang, target_lang)
    if not dataset:
        return {"pair": f"{source_lang}->{target_lang}", "samples": 0, "status": "no_data"}

    engine = get_translation_engine()
    total_bleu = 0.0
    total_purity = 0.0
    total_entity = 0.0
    total_latency = 0.0

    for item in dataset:
        src_text = item["source_text"]
        ref_text = item["target_text"]

        res = await engine.translate(src_text, source_lang, target_lang)

        bleu = calculate_word_overlap_bleu(ref_text, res.text)
        purity = calculate_script_purity(res.text, target_lang)
        ent = calculate_entity_preservation(src_text, res.text)

        total_bleu += bleu
        total_purity += purity
        total_entity += ent
        total_latency += res.latency_ms

    n = max(1, len(dataset))
    return {
        "pair": f"{source_lang.upper()} -> {target_lang.upper()}",
        "samples": len(dataset),
        "avg_bleu": round(total_bleu / n, 2),
        "script_purity": round((total_purity / n) * 100, 2),
        "entity_preservation": round(total_entity / n, 2),
        "avg_latency_ms": round(total_latency / n, 2),
    }


async def main():
    pairs = [
        ("en", "ta"), ("ta", "en"),
        ("en", "ml"), ("ml", "en"),
        ("en", "hi"), ("hi", "en"),
        ("en", "te"), ("te", "en"),
        ("en", "kn"), ("kn", "en"),
        ("ta", "ml"), ("ml", "ta"),
        ("ta", "hi"), ("hi", "ta"),
        ("en", "sat"), ("sat", "en"),
    ]

    print("==========================================================")
    print("TRANSLARA AI — TRANSLATION QUALITY & ACCURACY BENCHMARK")
    print("==========================================================")

    for src, tgt in pairs:
        result = await evaluate_pair(src, tgt)
        print(f"[{result['pair']}] BLEU: {result.get('avg_bleu', 0)}% | Script Purity: {result.get('script_purity', 0)}% | Entities: {result.get('entity_preservation', 0)}% | Latency: {result.get('avg_latency_ms', 0)} ms")

if __name__ == "__main__":
    asyncio.run(main())
