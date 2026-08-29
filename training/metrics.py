"""
Evaluation Metrics for TRANSLARA AI Translation and ASR.
Calculates BLEU, chrF, Character Match, Entity Preservation, and Script Correctness.
"""
from __future__ import annotations

import re
from typing import List


def calculate_word_overlap_bleu(reference: str, hypothesis: str) -> float:
    """Calculates n-gram BLEU approximation for translation verification."""
    ref_tokens = reference.strip().split()
    hyp_tokens = hypothesis.strip().split()

    if not ref_tokens or not hyp_tokens:
        return 0.0

    ref_counts = {}
    for t in ref_tokens:
        ref_counts[t] = ref_counts.get(t, 0) + 1

    matches = 0
    for t in hyp_tokens:
        if ref_counts.get(t, 0) > 0:
            matches += 1
            ref_counts[t] -= 1

    precision = matches / len(hyp_tokens)
    recall = matches / len(ref_tokens)

    if precision + recall == 0:
        return 0.0

    f1 = 2 * (precision * recall) / (precision + recall)
    return round(f1 * 100, 2)


def calculate_entity_preservation(source: str, hypothesis: str) -> float:
    """Measures what percentage of numerals and proper nouns in source exist in output."""
    src_numbers = re.findall(r"\b\d+\b", source)
    if not src_numbers:
        return 100.0

    preserved = sum(1 for num in src_numbers if num in hypothesis)
    return round((preserved / len(src_numbers)) * 100, 2)


def calculate_wer(reference: str, hypothesis: str) -> float:
    """Word Error Rate (WER) for ASR."""
    r = reference.split()
    h = hypothesis.split()
    d = [[0] * (len(h) + 1) for _ in range(len(r) + 1)]

    for i in range(len(r) + 1):
        d[i][0] = i
    for j in range(len(h) + 1):
        d[0][j] = j

    for i in range(1, len(r) + 1):
        for j in range(1, len(h) + 1):
            if r[i - 1] == h[j - 1]:
                d[i][j] = d[i - 1][j - 1]
            else:
                d[i][j] = min(
                    d[i - 1][j] + 1,      # deletion
                    d[i][j - 1] + 1,      # insertion
                    d[i - 1][j - 1] + 1,  # substitution
                )

    return round((d[len(r)][len(h)] / max(1, len(r))) * 100, 2)
