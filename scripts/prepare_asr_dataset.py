"""
Prepare ASR Dataset for TRANSLARA-ASR.

Usage:
    python scripts/prepare_asr_dataset.py --demo           # Generate CSV manifest for demo
    python scripts/prepare_asr_dataset.py --input <dir>    # Index audio files from directory
    python scripts/prepare_asr_dataset.py --validate --input data/asr/train/

Expected input directory structure:
    <dir>/
        ta/
            audio_001.wav
            audio_002.wav
        ml/
            audio_003.wav
        ...

A manifest CSV will be created:
    audio_file,language,transcript
    data/asr/train/ta/audio_001.wav,ta,<YOU MUST ADD TRANSCRIPTS>
"""
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac", ".ogg", ".m4a"}

LANGUAGE_MAP = {
    "ta": "Tamil", "ml": "Malayalam", "te": "Telugu",
    "kn": "Kannada", "hi": "Hindi", "en": "English",
    "sat": "Santhali", "hoc": "Ho", "unr": "Mundari",
}


def scan_audio_directory(audio_dir: Path) -> List[Dict]:
    """
    Recursively scan a directory for audio files.
    Infers language from subdirectory names (ta/, ml/, etc.).
    """
    records = []
    for fpath in sorted(audio_dir.rglob("*")):
        if fpath.suffix.lower() not in SUPPORTED_AUDIO_EXTENSIONS:
            continue
        # Try to infer language from parent dir name
        lang = fpath.parent.name.lower()
        if lang not in LANGUAGE_MAP:
            lang = "unknown"
        records.append({
            "audio_file": str(fpath),
            "language": lang,
            "transcript": "",  # User must fill in
        })
    return records


def write_manifest(records: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["audio_file", "language", "transcript"])
        writer.writeheader()
        writer.writerows(records)
    print(f"✅ Manifest written: {output_path} ({len(records)} files)")


def validate_manifest(manifest_path: Path) -> Dict:
    records = []
    if manifest_path.is_dir():
        csv_files = list(manifest_path.glob("*.csv"))
    else:
        csv_files = [manifest_path]

    for f in csv_files:
        with open(f, newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                records.append(row)

    missing_audio = [r for r in records if not Path(r.get("audio_file", "")).exists()]
    empty_transcripts = [r for r in records if not r.get("transcript", "").strip()]
    by_lang = {}
    for r in records:
        lang = r.get("language", "unknown")
        by_lang[lang] = by_lang.get(lang, 0) + 1

    return {
        "total_records": len(records),
        "valid_records": len(records) - len(missing_audio) - len(empty_transcripts),
        "missing_audio_files": len(missing_audio),
        "empty_transcripts": len(empty_transcripts),
        "by_language": by_lang,
        "warning": (
            f"{len(empty_transcripts)} records have no transcript. "
            "Fill in the 'transcript' column before training."
            if empty_transcripts else None
        ),
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare TRANSLARA ASR dataset")
    parser.add_argument("--input", type=str, help="Input audio directory or manifest CSV")
    parser.add_argument("--output", type=str, default="data/asr/train/manifest.csv")
    parser.add_argument("--demo", action="store_true",
                        help="Create an empty template manifest with instructions")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.demo:
        print("📦 Creating ASR manifest template...")
        template_records = [
            {
                "audio_file": "data/asr/train/ta/example_001.wav",
                "language": "ta",
                "transcript": "வணக்கம் மாணவர்களே இன்று நாம் கணிதம் கற்போம்",
            },
            {
                "audio_file": "data/asr/train/ml/example_001.wav",
                "language": "ml",
                "transcript": "നമസ്കാരം കുട്ടികളേ ഇന്ന് നാം ഗണിതം പഠിക്കും",
            },
            {
                "audio_file": "data/asr/train/hi/example_001.wav",
                "language": "hi",
                "transcript": "नमस्ते बच्चों आज हम गणित सीखेंगे",
            },
        ]
        out = ROOT / "data/asr/train/manifest_template.csv"
        write_manifest(template_records, out)
        print("\n📌 INSTRUCTIONS:")
        print("  1. Record/collect audio files in 16kHz mono WAV format")
        print("  2. Organize by language folder: data/asr/train/ta/, data/asr/train/ml/")
        print("  3. Fill in the 'transcript' column with the correct text")
        print("  4. Run: python -m training.train_asr --config config/training.yaml")
        return

    if args.validate and args.input:
        import json
        report = validate_manifest(Path(args.input))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.input:
        input_path = Path(args.input)
        if input_path.is_dir():
            records = scan_audio_directory(input_path)
            output_path = ROOT / args.output
            write_manifest(records, output_path)
            print(f"\n⚠️  {len(records)} audio files found.")
            print("   You MUST fill in the 'transcript' column before training.")
            print(f"   Edit: {output_path}")
        else:
            print(f"❌ Input directory not found: {input_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
