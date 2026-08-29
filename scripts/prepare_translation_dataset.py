"""
Prepare Translation Dataset for TRANSLARA-NMT.

Usage:
    python scripts/prepare_translation_dataset.py --input <your_csv_or_dir> --output data/translation/train/
    python scripts/prepare_translation_dataset.py --demo   # Generate sample data
    python scripts/prepare_translation_dataset.py --validate --input data/translation/train/
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))


# ============================================================
# Rich demo parallel corpus (classroom + educational context)
# ============================================================
DEMO_PAIRS = [
    # English → Tamil (classroom)
    ("en", "ta", "Good morning students", "காலை வணக்கம் மாணவர்களே"),
    ("en", "ta", "Open your books to page five", "உங்கள் புத்தகங்களை ஐந்தாம் பக்கத்தில் திறங்கள்"),
    ("en", "ta", "Today we will learn about numbers", "இன்று நாம் எண்களைப் பற்றி கற்போம்"),
    ("en", "ta", "One two three four five", "ஒன்று இரண்டு மூன்று நான்கு ஐந்து"),
    ("en", "ta", "The sun rises in the east", "சூரியன் கிழக்கில் உதிக்கிறது"),
    ("en", "ta", "Water is important for life", "தண்ணீர் உயிருக்கு மிகவும் முக்கியமானது"),
    ("en", "ta", "Wash your hands before eating", "சாப்பிடுவதற்கு முன் கைகளை கழுவுங்கள்"),
    ("en", "ta", "The cow gives us milk", "பசு நமக்கு பால் தருகிறது"),
    ("en", "ta", "A cat has four legs", "ஒரு பூனைக்கு நான்கு கால்கள் உள்ளன"),
    ("en", "ta", "My name is Raman", "என் பெயர் ராமன்"),

    # Tamil → English
    ("ta", "en", "வணக்கம்", "Hello"),
    ("ta", "en", "நன்றி", "Thank you"),
    ("ta", "en", "மாணவர்கள் படிக்கிறார்கள்", "The students are studying"),
    ("ta", "en", "ஆசிரியர் கற்பிக்கிறார்", "The teacher is teaching"),
    ("ta", "en", "பள்ளி நாளை மூடப்படும்", "School will be closed tomorrow"),

    # English → Malayalam
    ("en", "ml", "Good morning", "സുപ്രഭാതം"),
    ("en", "ml", "How are you", "നിങ്ങൾ എങ്ങനെ ഉണ്ട്"),
    ("en", "ml", "The children are playing", "കുട്ടികൾ കളിക്കുകയാണ്"),
    ("en", "ml", "Open your notebook", "നിങ്ങളുടെ നോട്ട്ബുക്ക് തുറക്കുക"),
    ("en", "ml", "Write your name", "നിങ്ങളുടെ പേര് എഴുതുക"),
    ("en", "ml", "Two plus two equals four", "രണ്ടും രണ്ടും നാലാണ്"),
    ("en", "ml", "The river flows to the sea", "നദി കടലിലേക്ക് ഒഴുകുന്നു"),
    ("en", "ml", "Birds fly in the sky", "പക്ഷികൾ ആകാശത്തിൽ പറക്കുന്നു"),

    # Malayalam → Tamil
    ("ml", "ta", "നമസ്കാരം", "வணக்கம்"),
    ("ml", "ta", "ഭക്ഷണം കഴിച്ചോ", "சாப்பிட்டீர்களா"),
    ("ml", "ta", "കുട്ടികൾ ഉറങ്ങുകയാണ്", "குழந்தைகள் தூங்குகிறார்கள்"),

    # Hindi → Tamil
    ("hi", "ta", "नमस्ते", "வணக்கம்"),
    ("hi", "ta", "आप कैसे हैं", "நீங்கள் எப்படி இருக்கிறீர்கள்"),
    ("hi", "ta", "बच्चे खेल रहे हैं", "குழந்தைகள் விளையாடுகிறார்கள்"),
    ("hi", "ta", "आज स्कूल बंद है", "இன்று பள்ளி மூடப்பட்டுள்ளது"),

    # English → Telugu
    ("en", "te", "Good morning", "శుభోదయం"),
    ("en", "te", "How are you", "మీరు ఎలా ఉన్నారు"),
    ("en", "te", "Students are learning", "విద్యార్థులు నేర్చుకుంటున్నారు"),
    ("en", "te", "The teacher explains", "ఉపాధ్యాయుడు వివరిస్తున్నాడు"),

    # English → Kannada
    ("en", "kn", "Good morning", "ಶುಭೋದಯ"),
    ("en", "kn", "How are you", "ನೀವು ಹೇಗಿದ್ದೀರಿ"),
    ("en", "kn", "Students are reading", "ವಿದ್ಯಾರ್ಥಿಗಳು ಓದುತ್ತಿದ್ದಾರೆ"),

    # English → Hindi
    ("en", "hi", "Good morning", "सुप्रभात"),
    ("en", "hi", "The students are studying", "छात्र पढ़ रहे हैं"),
    ("en", "hi", "Today is Monday", "आज सोमवार है"),
    ("en", "hi", "Read the book carefully", "किताब ध्यान से पढ़ो"),
    ("en", "hi", "Water is life", "जल ही जीवन है"),
]


def write_csv(pairs: List[tuple], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["src_lang", "tgt_lang", "src_text", "tgt_text"])
        writer.writeheader()
        for src_lang, tgt_lang, src_text, tgt_text in pairs:
            writer.writerow({
                "src_lang": src_lang,
                "tgt_lang": tgt_lang,
                "src_text": src_text,
                "tgt_text": tgt_text,
            })
    print(f"✅ Wrote {len(pairs)} pairs → {output_path}")


def validate_csv(input_path: Path) -> Dict:
    pairs = []
    csv_files = list(input_path.glob("*.csv")) if input_path.is_dir() else [input_path]
    for f in csv_files:
        with open(f, newline="", encoding="utf-8") as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                pairs.append(row)

    echo = [r for r in pairs if r.get("src_text", "").strip() == r.get("tgt_text", "").strip()]
    empty = [r for r in pairs if not r.get("src_text", "").strip() or not r.get("tgt_text", "").strip()]

    by_pair: Dict[str, int] = {}
    for r in pairs:
        key = f"{r.get('src_lang','?')}->{r.get('tgt_lang','?')}"
        by_pair[key] = by_pair.get(key, 0) + 1

    return {
        "total": len(pairs),
        "valid": len(pairs) - len(echo) - len(empty),
        "echo_pairs_rejected": len(echo),
        "empty_pairs_rejected": len(empty),
        "by_language_pair": by_pair,
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare TRANSLARA translation dataset")
    parser.add_argument("--input", type=str, help="Input CSV file or directory")
    parser.add_argument("--output", type=str, default="data/translation/train/",
                        help="Output directory for prepared dataset")
    parser.add_argument("--demo", action="store_true",
                        help="Generate sample demo dataset (no input required)")
    parser.add_argument("--validate", action="store_true",
                        help="Validate existing CSV files in --input directory")
    args = parser.parse_args()

    if args.demo:
        print("📦 Generating TRANSLARA demo translation dataset...")
        train_pairs = DEMO_PAIRS[:int(len(DEMO_PAIRS) * 0.8)]
        val_pairs = DEMO_PAIRS[int(len(DEMO_PAIRS) * 0.8):]
        test_pairs = DEMO_PAIRS[:5]

        write_csv(train_pairs, ROOT / "data/translation/train/demo_pairs.csv")
        write_csv(val_pairs, ROOT / "data/translation/validation/demo_pairs.csv")
        write_csv(test_pairs, ROOT / "data/translation/test/demo_pairs.csv")

        print("\n📌 NOTE: This is DEMO DATA for testing the pipeline.")
        print("   Replace with your real parallel corpus for actual training.")
        print("\n   To add your data:")
        print("   1. Create a CSV with columns: src_lang,tgt_lang,src_text,tgt_text")
        print("   2. Copy it to: data/translation/train/")
        print("   3. Run: python -m training.train_translation --config config/training.yaml")
        return

    if args.validate and args.input:
        report = validate_csv(Path(args.input))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.input:
        input_path = Path(args.input)
        output_path = Path(args.output) / "imported_data.csv"
        if input_path.is_file():
            report = validate_csv(input_path)
            print(f"Validation: {json.dumps(report, indent=2)}")
            # Copy validated file
            import shutil
            output_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(input_path, output_path)
            print(f"✅ Data prepared: {output_path}")
        else:
            print(f"❌ Input path not found: {input_path}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
