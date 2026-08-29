"""
Training, Fine-Tuning & Evaluation utilities for TRANSLARA AI.

Custom trainable components:
    - TRANSLARA-ASR   (Whisper fine-tuning):         train_asr.py
    - TRANSLARA-NMT   (NLLB-200 fine-tuning):        train_translation.py
    - TRANSLARA-NER   (XLM-RoBERTa fine-tuning):     train_ner.py
    - TRANSLARA-TTS   (MMS-TTS VITS fine-tuning):    train_tts.py
    - TRANSLARA-EDU   (Qwen2.5+LoRA fine-tuning):    train_education.py

Usage (run from project root):
    python -m training.train_translation --config config/training.yaml
    python -m training.train_asr         --config config/training.yaml
    python -m training.train_ner         --config config/training.yaml
    python -m training.train_tts         --config config/training.yaml --language ta
    python -m training.train_education   --config config/training.yaml

Dry-run validation (no model download required):
    python -m training.train_translation --config config/training.yaml --dry-run
    python -m training.train_asr         --config config/training.yaml --dry-run
    python -m training.train_ner         --config config/training.yaml --dry-run
    python -m training.train_education   --config config/training.yaml --dry-run

Dataset preparation:
    python scripts/prepare_translation_dataset.py --demo
    python scripts/prepare_asr_dataset.py         --demo
    python scripts/prepare_ner_dataset.py         --demo
    python scripts/prepare_tts_dataset.py         --demo
    python scripts/prepare_education_dataset.py   --demo

Model registry check:
    python scripts/verify_ai_system.py
"""
from training.dataset_prep import load_dataset, split_dataset
from training.metrics import (
    calculate_entity_preservation,
    calculate_wer,
    calculate_word_overlap_bleu,
)

__all__ = [
    "load_dataset",
    "split_dataset",
    "calculate_word_overlap_bleu",
    "calculate_entity_preservation",
    "calculate_wer",
]
