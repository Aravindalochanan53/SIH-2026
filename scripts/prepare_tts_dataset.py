"""
Prepare TTS Dataset for TRANSLARA-TTS.

Usage:
    python scripts/prepare_tts_dataset.py --demo
    python scripts/prepare_tts_dataset.py --input <audio_dir> --output data/tts/train/
    python scripts/prepare_tts_dataset.py --validate --input data/tts/train/

CSV format:
    text,audio_path,language,speaker_id
    வணக்கம்,data/tts/train/ta/001.wav,ta,speaker1
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

SUPPORTED_AUDIO_EXTENSIONS = {".wav", ".mp3", ".flac"}

# Demo TTS text samples by language (no audio — user must record)
DEMO_TTS_TEXT = {
    "ta": [
        "வணக்கம் மாணவர்களே.",
        "இன்று நாம் கணிதம் கற்போம்.",
        "ஒன்று இரண்டு மூன்று நான்கு ஐந்து.",
        "நீர் நமது உயிர்.",
        "பள்ளிக்கு தினமும் வாருங்கள்.",
    ],
    "ml": [
        "നമസ്കാരം കുട്ടികളേ.",
        "ഇന്ന് നാം ഗണിതം പഠിക്കും.",
        "ഒന്ന് രണ്ട് മൂന്ന് നാല് അഞ്ച്.",
        "ജലം ജീവൻ ആണ്.",
        "എല്ലാ ദിവസവും സ്കൂളിൽ വരുക.",
    ],
    "hi": [
        "नमस्ते बच्चों.",
        "आज हम गणित सीखेंगे.",
        "एक दो तीन चार पाँच.",
        "जल ही जीवन है.",
        "हर रोज़ स्कूल आओ.",
    ],
    "en": [
        "Good morning students.",
        "Today we will learn mathematics.",
        "One two three four five.",
        "Water is life.",
        "Come to school every day.",
    ],
    "te": [
        "శుభోదయం విద్యార్థులూ.",
        "ఇప్పుడు మనం గణితం నేర్చుకుందాం.",
        "ఒకటి రెండు మూడు నాలుగు ఐదు.",
    ],
    "kn": [
        "ಶುಭೋದಯ ವಿದ್ಯಾರ್ಥಿಗಳೇ.",
        "ಇಂದು ನಾವು ಗಣಿತ ಕಲಿಯೋಣ.",
        "ಒಂದು ಎರಡು ಮೂರು ನಾಲ್ಕು ಐದು.",
    ],
}


def create_template_csv(language: str, output_dir: Path):
    """Create a TTS manifest template CSV with placeholder audio paths."""
    texts = DEMO_TTS_TEXT.get(language, [])
    rows = []
    lang_dir = output_dir / language
    lang_dir.mkdir(parents=True, exist_ok=True)

    for i, text in enumerate(texts, start=1):
        audio_filename = f"speaker1_{i:03d}.wav"
        audio_path = str(lang_dir / audio_filename)
        rows.append({
            "text": text,
            "audio_path": audio_path,
            "language": language,
            "speaker_id": "speaker1",
        })

    csv_path = output_dir.parent / f"manifest_{language}.csv"
    with open(csv_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "audio_path", "language", "speaker_id"])
        writer.writeheader()
        writer.writerows(rows)

    return csv_path, rows


def scan_and_build_manifest(audio_dir: Path, language: str, output_csv: Path):
    """Scan audio directory and build a TTS manifest."""
    audio_files = []
    for ext in SUPPORTED_AUDIO_EXTENSIONS:
        audio_files.extend(sorted(audio_dir.rglob(f"*{ext}")))

    rows = []
    for fpath in audio_files:
        # Try to read matching text from a .txt file with same stem
        txt_path = fpath.with_suffix(".txt")
        text = txt_path.read_text(encoding="utf-8").strip() if txt_path.exists() else ""
        rows.append({
            "text": text,
            "audio_path": str(fpath),
            "language": language,
            "speaker_id": "speaker1",
        })

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["text", "audio_path", "language", "speaker_id"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"✅ Manifest: {output_csv} ({len(rows)} files)")
    if any(not r["text"] for r in rows):
        missing = sum(1 for r in rows if not r["text"])
        print(f"⚠️  {missing} audio files have no transcript (.txt sidecar).")
        print("   Create a .txt file next to each .wav with the spoken text.")
    return rows


def validate_manifest(csv_path: Path) -> Dict:
    records = []
    csv_files = list(csv_path.glob("*.csv")) if csv_path.is_dir() else [csv_path]
    for f in csv_files:
        with open(f, newline="", encoding="utf-8") as fp:
            records.extend(list(csv.DictReader(fp)))

    missing_audio = [r for r in records if not Path(r.get("audio_path", "")).exists()]
    empty_text = [r for r in records if not r.get("text", "").strip()]
    by_lang: Dict[str, int] = {}
    for r in records:
        lang = r.get("language", "?")
        by_lang[lang] = by_lang.get(lang, 0) + 1

    return {
        "total": len(records),
        "valid": len(records) - len(missing_audio) - len(empty_text),
        "missing_audio": len(missing_audio),
        "empty_text": len(empty_text),
        "by_language": by_lang,
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare TRANSLARA-TTS dataset")
    parser.add_argument("--demo", action="store_true",
                        help="Create template manifests for all supported languages")
    parser.add_argument("--input", type=str, help="Audio directory to scan")
    parser.add_argument("--language", type=str, default="ta", help="Language code")
    parser.add_argument("--output", type=str, default="data/tts/train/")
    parser.add_argument("--validate", action="store_true")
    args = parser.parse_args()

    if args.demo:
        print("📦 Generating TTS manifest templates for all languages...")
        for lang in DEMO_TTS_TEXT:
            out_dir = ROOT / "data/tts/train"
            csv_path, rows = create_template_csv(lang, out_dir)
            print(f"  {lang}: {csv_path} ({len(rows)} entries)")
        print("\n📌 INSTRUCTIONS:")
        print("  1. Record audio files at 22050 Hz mono WAV")
        print("  2. Replace placeholder paths in manifest CSV with real paths")
        print("  3. Run: python -m training.train_tts --config config/training.yaml --language ta")
        return

    if args.validate and args.input:
        import json
        report = validate_manifest(Path(args.input))
        print(json.dumps(report, indent=2))
        return

    if args.input:
        audio_dir = Path(args.input)
        output_csv = ROOT / args.output / f"manifest_{args.language}.csv"
        scan_and_build_manifest(audio_dir, args.language, output_csv)
        return

    parser.print_help()


if __name__ == "__main__":
    main()
