"""
Prepare NER Dataset for TRANSLARA-NER.

Usage:
    python scripts/prepare_ner_dataset.py --demo     # Generate sample JSONL
    python scripts/prepare_ner_dataset.py --validate --input data/ner/train/
    python scripts/prepare_ner_dataset.py --convert --input <conll_file> --output data/ner/train/

Dataset format (JSONL):
    {"tokens": ["ராமன்", "தஞ்சாவூர்", "பள்ளியில்", "படிக்கிறான்"],
     "ner_tags": ["B-PERSON", "B-LOCATION", "B-SCHOOL", "O"],
     "language": "ta"}
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

NER_LABELS = [
    "O", "B-PERSON", "I-PERSON", "B-LOCATION", "I-LOCATION",
    "B-VILLAGE", "I-VILLAGE", "B-SCHOOL", "I-SCHOOL",
    "B-ORGANIZATION", "I-ORGANIZATION", "B-NUMBER", "I-NUMBER",
    "B-DATE", "I-DATE", "B-TIME", "I-TIME",
    "B-CLASS", "I-CLASS", "B-SUBJECT", "I-SUBJECT",
]

# ============================================================
# Rich demo NER samples
# ============================================================
DEMO_NER_SAMPLES = [
    # Tamil
    {
        "tokens": ["ராமன்", "தஞ்சாவூர்", "மாவட்டத்தில்", "உள்ள", "அரசு", "பள்ளியில்", "படிக்கிறான்"],
        "ner_tags": ["B-PERSON", "B-LOCATION", "I-LOCATION", "O", "O", "B-SCHOOL", "O"],
        "language": "ta",
    },
    {
        "tokens": ["முதல்", "வகுப்பு", "மாணவர்கள்", "இன்று", "கணிதம்", "கற்றனர்"],
        "ner_tags": ["B-CLASS", "I-CLASS", "O", "B-DATE", "B-SUBJECT", "O"],
        "language": "ta",
    },
    {
        "tokens": ["ஆசிரியை", "சுமதி", "காலை", "8", "மணிக்கு", "வந்தார்"],
        "ner_tags": ["O", "B-PERSON", "O", "B-TIME", "I-TIME", "O"],
        "language": "ta",
    },
    {
        "tokens": ["இந்த", "பள்ளியில்", "200", "மாணவர்கள்", "படிக்கின்றனர்"],
        "ner_tags": ["O", "B-SCHOOL", "B-NUMBER", "O", "O"],
        "language": "ta",
    },
    # Malayalam
    {
        "tokens": ["രാമൻ", "തൃശ്ശൂർ", "ജില്ലയിലെ", "ഗവൺമെന്റ്", "സ്കൂളിൽ", "പഠിക്കുന്നു"],
        "ner_tags": ["B-PERSON", "B-LOCATION", "I-LOCATION", "O", "B-SCHOOL", "O"],
        "language": "ml",
    },
    {
        "tokens": ["ഒന്നാം", "ക്ലാസ്സ്", "വിദ്യാർത്ഥികൾ", "ഇന്ന്", "ഗണിതം", "പഠിച്ചു"],
        "ner_tags": ["B-CLASS", "I-CLASS", "O", "B-DATE", "B-SUBJECT", "O"],
        "language": "ml",
    },
    {
        "tokens": ["അധ്യാപിക", "സുമ", "ഉച്ചയ്ക്ക്", "12", "മണിക്ക്", "വന്നു"],
        "ner_tags": ["O", "B-PERSON", "O", "B-TIME", "I-TIME", "O"],
        "language": "ml",
    },
    # English
    {
        "tokens": ["Raman", "studies", "at", "Government", "Primary", "School", "in", "Chennai"],
        "ner_tags": ["B-PERSON", "O", "O", "B-SCHOOL", "I-SCHOOL", "I-SCHOOL", "O", "B-LOCATION"],
        "language": "en",
    },
    {
        "tokens": ["Grade", "1", "students", "are", "learning", "Mathematics", "today"],
        "ner_tags": ["B-CLASS", "I-CLASS", "O", "O", "O", "B-SUBJECT", "B-DATE"],
        "language": "en",
    },
    {
        "tokens": ["The", "teacher", "Suma", "arrived", "at", "8", "AM"],
        "ner_tags": ["O", "O", "B-PERSON", "O", "O", "B-TIME", "I-TIME"],
        "language": "en",
    },
    # Hindi
    {
        "tokens": ["राम", "तमिलनाडु", "के", "एक", "सरकारी", "स्कूल", "में", "पढ़ता", "है"],
        "ner_tags": ["B-PERSON", "B-LOCATION", "O", "O", "O", "B-SCHOOL", "O", "O", "O"],
        "language": "hi",
    },
    {
        "tokens": ["कक्षा", "एक", "के", "छात्र", "आज", "गणित", "सीख", "रहे", "हैं"],
        "ner_tags": ["B-CLASS", "I-CLASS", "O", "O", "B-DATE", "B-SUBJECT", "O", "O", "O"],
        "language": "hi",
    },
    # Telugu
    {
        "tokens": ["రాముడు", "తిరుపతి", "లోని", "ప్రభుత్వ", "పాఠశాలలో", "చదువుతున్నాడు"],
        "ner_tags": ["B-PERSON", "B-LOCATION", "O", "O", "B-SCHOOL", "O"],
        "language": "te",
    },
    # Kannada
    {
        "tokens": ["ರಾಮ", "ಬೆಂಗಳೂರಿನ", "ಸರ್ಕಾರಿ", "ಶಾಲೆಯಲ್ಲಿ", "ಓದುತ್ತಿದ್ದಾನೆ"],
        "ner_tags": ["B-PERSON", "B-LOCATION", "O", "B-SCHOOL", "O"],
        "language": "kn",
    },
]


def write_jsonl(samples: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"✅ Wrote {len(samples)} samples → {output_path}")


def validate_jsonl_dir(data_dir: Path) -> Dict:
    samples = []
    jsonl_files = list(data_dir.glob("*.jsonl")) + list(data_dir.glob("**/*.jsonl"))
    errors = []

    for jf in jsonl_files:
        with open(jf, encoding="utf-8") as f:
            for i, line in enumerate(f):
                line = line.strip()
                if not line:
                    continue
                try:
                    obj = json.loads(line)
                    tokens = obj.get("tokens", [])
                    tags = obj.get("ner_tags", [])
                    if len(tokens) != len(tags):
                        errors.append(f"{jf}:{i+1} — token/tag length mismatch")
                    unknown = [t for t in tags if t not in NER_LABELS]
                    if unknown:
                        errors.append(f"{jf}:{i+1} — unknown tags: {unknown}")
                    samples.append(obj)
                except json.JSONDecodeError as e:
                    errors.append(f"{jf}:{i+1} — JSON error: {e}")

    by_lang = {}
    for s in samples:
        lang = s.get("language", "?")
        by_lang[lang] = by_lang.get(lang, 0) + 1

    return {
        "total_sentences": len(samples),
        "errors": len(errors),
        "error_details": errors[:10],
        "by_language": by_lang,
        "supported_labels": NER_LABELS,
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare TRANSLARA NER dataset")
    parser.add_argument("--demo", action="store_true", help="Generate sample JSONL data")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--input", type=str)
    parser.add_argument("--output", type=str, default="data/ner/train/demo.jsonl")
    args = parser.parse_args()

    if args.demo:
        print("📦 Generating TRANSLARA NER demo dataset...")
        n = len(DEMO_NER_SAMPLES)
        train = DEMO_NER_SAMPLES[:int(n * 0.8)]
        val = DEMO_NER_SAMPLES[int(n * 0.8):]

        write_jsonl(train, ROOT / "data/ner/train/demo.jsonl")
        write_jsonl(val, ROOT / "data/ner/validation/demo.jsonl")
        write_jsonl(DEMO_NER_SAMPLES[:5], ROOT / "data/ner/test/demo.jsonl")

        print("\n📌 Supported entity labels:")
        for label in NER_LABELS:
            print(f"   {label}")
        return

    if args.validate and args.input:
        report = validate_jsonl_dir(Path(args.input))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    parser.print_help()


if __name__ == "__main__":
    main()
