"""
Dataset Preparation & Preprocessing for TRANSLARA Domain Adaptation.
Loads JSONL parallel translation datasets and splits into Train/Val/Test.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Tuple

DEFAULT_DATA_DIR = Path(r"c:\Users\admin\OneDrive\Documents\SIH-2026\data\translation")


def load_dataset(source_lang: str, target_lang: str, data_dir: Path = DEFAULT_DATA_DIR) -> List[Dict[str, str]]:
    file_path = data_dir / f"{source_lang}_{target_lang}.jsonl"
    if not file_path.exists():
        return []

    records = []
    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def split_dataset(
    records: List[Dict[str, str]],
    train_ratio: float = 0.8,
    val_ratio: float = 0.1,
) -> Tuple[List[Dict[str, str]], List[Dict[str, str]], List[Dict[str, str]]]:
    n = len(records)
    n_train = int(n * train_ratio)
    n_val = int(n * val_ratio)

    train = records[:n_train]
    val = records[n_train : n_train + n_val]
    test = records[n_train + n_val :]
    return train, val, test
