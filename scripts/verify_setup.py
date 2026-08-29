"""
Verification Script for TRANSLARA.
Run: python scripts/verify_setup.py
"""
import sys
import asyncio
from pathlib import Path

# Fix Windows console UTF-8 output
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.config import settings
from backend.ml_engine.entity_lock import EntityLock
from backend.ml_engine.pipeline import run_pipeline
from backend.ml_engine.languages import get_language, get_capabilities_matrix
from backend.pedagogy.flashcard_generator import generate_flashcard_pdf
from backend.pedagogy.content_bank import SEED_ENTRIES
from backend.cache.database import init_db
from backend.cache.seed_cache import seed_all


async def verify_all():
    print("=" * 60)
    print("TRANSLARA — MULTILINGUAL SYSTEM VERIFICATION")
    print("=" * 60)

    # 1. Config Check
    print(f"[1/7] Config: MOCK_MODE={settings.mock_mode}, DEMO_MODE={settings.demo_mode}")
    print(f"      ASR: {settings.asr_backend} | NMT: {settings.nmt_backend} | TTS: {settings.tts_backend}")

    # 2. Language Registry Check
    ta = get_language("ta")
    ml = get_language("ml")
    assert ta and ta.native_name == "தமிழ்"
    assert ml and ml.native_name == "മലയാളം"
    matrix = get_capabilities_matrix()
    assert "ta" in matrix and "ml" in matrix
    print(f"[2/7] Language Registry: Verified! (Tamil: {ta.native_name}, Malayalam: {ml.native_name})")

    # 3. Database & Seed Check
    init_db()
    p_cnt, e_cnt = seed_all()
    print(f"[3/7] SQLite DB Initialized & Seeded: {p_cnt} phrases, {e_cnt} entities")

    # 4. South Indian Entity Lock Check
    lock = EntityLock()
    test_sentence = "அருணிடம் 5 புத்தகங்கள் உள்ளன."
    detected = lock.detect_entities(test_sentence)
    names = [e.text for e in detected if e.kind.value == "PERSON"]
    nums = [e.text for e in detected if e.kind.value == "NUMBER"]
    assert "5" in nums, "Failed to lock numeral 5"
    print(f"[4/7] Entity Lock Shield: Verified! Protected: {names} and {nums}")

    # 5. Pipeline Execution Check (Tamil -> Malayalam)
    dummy_pcm = b"\x00" * 32000
    res = await run_pipeline(dummy_pcm, "ta", "ml")
    assert res.translation, "Pipeline returned empty translation"
    print(f"[5/7] End-to-End Pipeline (ta -> ml): Verified! (Latency: {res.total_latency_ms:.1f}ms)")
    print(f"      Transcript: '{res.transcript}' -> Translation: '{res.translation}'")

    # 6. Pedagogy PDF Check (Tamil & Malayalam)
    out_pdf = Path("./backend/assets/translara_pdfs/verify_flashcards.pdf")
    generate_flashcard_pdf(SEED_ENTRIES[:4], source_lang="ta", target_lang="ml", output_path=out_pdf)
    assert out_pdf.exists(), "Flashcard PDF not created"
    print(f"[6/7] Pedagogy Engine: Verified! Generated PDF at: {out_pdf}")

    # 7. Extension Check
    ext_manifest = Path("./extension/manifest.json")
    assert ext_manifest.exists(), "Extension manifest not found"
    print(f"[7/7] Chrome Extension: Manifest V3 ready at: {ext_manifest}")

    print("=" * 60)
    print("ALL 7 ACCEPTANCE CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(verify_all())
