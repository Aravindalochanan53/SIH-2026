"""
Prepare Education Dataset for TRANSLARA-EDU.

Usage:
    python scripts/prepare_education_dataset.py --demo
    python scripts/prepare_education_dataset.py --validate --input data/education/
    python scripts/prepare_education_dataset.py --input <your_jsonl> --output data/education/
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import List, Dict

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# ============================================================
# Rich educational Q&A demo data (Grades 1-3, multiple Indian languages)
# ============================================================
DEMO_EDU_SAMPLES = [
    # Grade 1 — Mathematics — Tamil
    {"grade": 1, "subject": "Mathematics", "topic": "Numbers 1-10", "language": "ta",
     "instruction": "1 முதல் 5 வரை தமிழில் சொல்லுங்கள்",
     "response": "ஒன்று, இரண்டு, மூன்று, நான்கு, ஐந்து"},
    {"grade": 1, "subject": "Mathematics", "topic": "Addition", "language": "ta",
     "instruction": "2 + 3 என்பதை ஒரு கதையாக சொல்லுங்கள்",
     "response": "இரண்டு ஆடுகளுடன் மூன்று ஆடுகள் சேர்ந்தால் ஐந்து ஆடுகள் ஆகும்."},
    {"grade": 1, "subject": "Science", "topic": "Animals", "language": "ta",
     "instruction": "பண்ணை விலங்குகளின் பெயர்களை சொல்லுங்கள்",
     "response": "பசு, ஆடு, கோழி, நாய், பூனை ஆகியவை பண்ணை விலங்குகள்."},

    # Grade 1 — Malayalam
    {"grade": 1, "subject": "Mathematics", "topic": "Numbers 1-10", "language": "ml",
     "instruction": "1 മുതൽ 5 വരെ മലയാളത്തിൽ പറയുക",
     "response": "ഒന്ന്, രണ്ട്, മൂന്ന്, നാല്, അഞ്ച്"},
    {"grade": 1, "subject": "Science", "topic": "Plants", "language": "ml",
     "instruction": "ചെടികൾക്ക് എന്ത് വേണം?",
     "response": "ചെടികൾക്ക് വെള്ളം, വെളിച്ചം, വായു, മണ്ണ് ഇവ വേണം."},
    {"grade": 1, "subject": "Language", "topic": "Alphabets", "language": "ml",
     "instruction": "മലയാളം അക്ഷരമാലയിലെ ആദ്യ 3 അക്ഷരങ്ങൾ",
     "response": "അ, ആ, ഇ - ഇവയാണ് ആദ്യ മൂന്ന് അക്ഷരങ്ങൾ."},

    # Grade 2 — English
    {"grade": 2, "subject": "Mathematics", "topic": "Multiplication", "language": "en",
     "instruction": "Explain 2 times table to a Grade 2 student simply",
     "response": "2 times table: 2×1=2, 2×2=4, 2×3=6, 2×4=8, 2×5=10. Think of it as pairs!"},
    {"grade": 2, "subject": "Science", "topic": "Water cycle", "language": "en",
     "instruction": "What is the water cycle? Explain simply for Grade 2",
     "response": "Water from lakes goes up as steam when heated by sun. It forms clouds. "
                 "Then it falls as rain. This circle is called the water cycle."},
    {"grade": 2, "subject": "Language", "topic": "Sentences", "language": "en",
     "instruction": "What makes a good sentence?",
     "response": "A good sentence has a subject (who/what) and a verb (action). "
                 "Example: 'The dog runs.' Dog is the subject, runs is the verb."},

    # Grade 2 — Hindi
    {"grade": 2, "subject": "Mathematics", "topic": "Addition", "language": "hi",
     "instruction": "5 + 7 कैसे जोड़ें? सरल तरीके से समझाएं",
     "response": "पहले 5 उंगलियां गिनो, फिर 7 और उंगलियां गिनो। कुल मिलाकर 12 उंगलियां हैं। "
                 "तो 5 + 7 = 12"},
    {"grade": 2, "subject": "Science", "topic": "Animals", "language": "hi",
     "instruction": "जंगली जानवरों के नाम बताओ",
     "response": "शेर, बाघ, हाथी, हिरण, बंदर ये सब जंगली जानवर हैं।"},

    # Grade 3 — Tamil — Science
    {"grade": 3, "subject": "Science", "topic": "Solar system", "language": "ta",
     "instruction": "சூரியக் குடும்பத்தில் எத்தனை கோள்கள் உள்ளன?",
     "response": "சூரியக் குடும்பத்தில் 8 கோள்கள் உள்ளன: "
                 "புதன், வெள்ளி, பூமி, செவ்வாய், வியாழன், சனி, யுரேனஸ், நெப்டியூன்."},
    {"grade": 3, "subject": "Mathematics", "topic": "Division", "language": "ta",
     "instruction": "10 ÷ 2 என்றால் என்ன என்று கதையாக சொல்லுங்கள்",
     "response": "10 மாம்பழங்களை 2 பிள்ளைகளுக்கு சமனாக பிரித்தால், ஒவ்வொருவருக்கும் 5 மாம்பழங்கள் கிடைக்கும். "
                 "எனவே 10 ÷ 2 = 5."},

    # Grade 3 — Malayalam — Science
    {"grade": 3, "subject": "Science", "topic": "Human body", "language": "ml",
     "instruction": "മനുഷ്യ ശരീരത്തിലെ അവയവങ്ങൾ ഏതൊക്കെ?",
     "response": "ഹൃദയം, ശ്വാസകോശം, തലച്ചോറ്, കരൾ, വൃക്ക ഇവ പ്രധാന ആന്തരിക അവയവങ്ങൾ ആണ്."},

    # Grade 1 — Telugu
    {"grade": 1, "subject": "Mathematics", "topic": "Numbers 1-5", "language": "te",
     "instruction": "1 నుండి 5 వరకు తెలుగులో చెప్పండి",
     "response": "ఒకటి, రెండు, మూడు, నాలుగు, ఐదు"},

    # Grade 1 — Kannada
    {"grade": 1, "subject": "Mathematics", "topic": "Numbers 1-5", "language": "kn",
     "instruction": "1 ರಿಂದ 5 ರವರೆಗೆ ಕನ್ನಡದಲ್ಲಿ ಹೇಳಿ",
     "response": "ಒಂದು, ಎರಡು, ಮೂರು, ನಾಲ್ಕು, ಐದು"},

    # Grade 2 — English — pedagogy
    {"grade": 2, "subject": "EVS", "topic": "Environment", "language": "en",
     "instruction": "Why should we not cut trees?",
     "response": "Trees give us oxygen to breathe, fruits to eat, and wood to build. "
                 "They also keep the air clean and give shade. "
                 "Cutting trees harms birds and animals who live in them. "
                 "We should plant more trees instead!"},

    # Grade 3 — Hindi — Language
    {"grade": 3, "subject": "Hindi", "topic": "Story writing", "language": "hi",
     "instruction": "एक छोटी कहानी लिखो जिसमें एक चतुर खरगोश हो",
     "response": "एक जंगल में एक चतुर खरगोश रहता था। एक दिन शेर ने उसे खाना चाहा। "
                 "खरगोश ने कहा, 'राजा जी, एक और शेर ने कहा वह इस जंगल का राजा है!' "
                 "शेर गुस्से में कुएं के पास गया। पानी में अपनी परछाई देखकर वह चिल्लाया "
                 "और कुएं में कूद पड़ा। खरगोश खुशी से घर चला गया।"},
]


def write_jsonl(samples: List[Dict], output_path: Path):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        for s in samples:
            f.write(json.dumps(s, ensure_ascii=False) + "\n")
    print(f"✅ Wrote {len(samples)} samples → {output_path}")


def validate_education_data(data_dir: Path) -> Dict:
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
                    instr = obj.get("instruction", "").strip()
                    resp = obj.get("response", "").strip()
                    if not instr or not resp:
                        errors.append(f"{jf}:{i+1} — empty instruction or response")
                    if instr == resp:
                        errors.append(f"{jf}:{i+1} — echo: instruction == response")
                    samples.append(obj)
                except json.JSONDecodeError as e:
                    errors.append(f"{jf}:{i+1} — JSON error: {e}")

    by_lang: Dict[str, int] = {}
    by_grade: Dict[str, int] = {}
    by_subject: Dict[str, int] = {}
    for s in samples:
        for d, k in [(by_lang, "language"), (by_grade, "grade"), (by_subject, "subject")]:
            key = str(s.get(k, "?"))
            d[key] = d.get(key, 0) + 1

    return {
        "total": len(samples),
        "valid": len(samples) - len(errors),
        "errors": len(errors),
        "error_details": errors[:10],
        "by_language": by_lang,
        "by_grade": by_grade,
        "by_subject": by_subject,
    }


def main():
    parser = argparse.ArgumentParser(description="Prepare TRANSLARA-EDU dataset")
    parser.add_argument("--demo", action="store_true", help="Generate demo JSONL dataset")
    parser.add_argument("--validate", action="store_true")
    parser.add_argument("--input", type=str, help="Input JSONL or directory")
    parser.add_argument("--output", type=str, default="data/education/train/")
    args = parser.parse_args()

    if args.demo:
        print("📦 Generating TRANSLARA-EDU demo dataset...")
        n = len(DEMO_EDU_SAMPLES)
        train = DEMO_EDU_SAMPLES[:int(n * 0.8)]
        val = DEMO_EDU_SAMPLES[int(n * 0.8):]

        write_jsonl(train, ROOT / "data/education/train/demo.jsonl")
        write_jsonl(val, ROOT / "data/education/validation/demo.jsonl")
        write_jsonl(DEMO_EDU_SAMPLES[:5], ROOT / "data/education/test/demo.jsonl")
        print("\n📌 Required JSONL fields: grade, subject, topic, language, instruction, response")
        print("   Add your own data to data/education/train/ as JSONL files.")
        return

    if args.validate and args.input:
        report = validate_education_data(Path(args.input))
        print(json.dumps(report, indent=2, ensure_ascii=False))
        return

    if args.input:
        src = Path(args.input)
        out = ROOT / args.output
        out.mkdir(parents=True, exist_ok=True)
        import shutil
        if src.is_file():
            shutil.copy2(src, out / src.name)
            print(f"✅ Copied {src} → {out / src.name}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
