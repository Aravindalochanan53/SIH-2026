"""
Unit tests for TRANSLARA Language Registry and Capabilities Matrix.
"""
from backend.ml_engine.languages import (
    LANGUAGES,
    get_all_languages,
    get_capabilities_matrix,
    get_grouped_languages,
    get_language,
    is_pair_supported,
)


def test_language_registry_contains_required_languages():
    """TEST 20: Language registry contains all required South and North Indian languages."""
    required = ["ta", "te", "kn", "ml", "hi", "sat", "hoc", "unr"]
    for code in required:
        lang = get_language(code)
        assert lang is not None, f"Language code {code} missing from registry"
        assert lang.name is not None
        assert lang.native_name is not None
        assert lang.region is not None

    # Verify South Indian language details
    ta = get_language("ta")
    assert ta.name == "Tamil"
    assert ta.native_name == "தமிழ்"
    assert ta.region == "South India"

    ml = get_language("ml")
    assert ml.name == "Malayalam"
    assert ml.native_name == "മലയാളം"
    assert ml.region == "South India"

    te = get_language("te")
    assert te.name == "Telugu"
    assert te.native_name == "తెలుగు"

    kn = get_language("kn")
    assert kn.name == "Kannada"
    assert kn.native_name == "ಕನ್ನಡ"


def test_grouped_languages_prominently_features_south_india():
    """Verify UI grouping has South India with all 4 Dravidian languages."""
    grouped = get_grouped_languages()
    assert "South India" in grouped
    south_codes = [item["code"] for item in grouped["South India"]]
    assert "ta" in south_codes
    assert "te" in south_codes
    assert "kn" in south_codes
    assert "ml" in south_codes


def test_capabilities_matrix():
    """TEST 21: Capabilities matrix reports support accurately."""
    matrix = get_capabilities_matrix()
    assert "ta" in matrix
    assert matrix["ta"]["asr"] is True
    assert matrix["ta"]["translation"] is True
    assert matrix["ta"]["tts"] is True

    assert "ml" in matrix
    assert matrix["ml"]["translation"] is True

    # Check pair support validation
    assert is_pair_supported("ta", "ml") is True
    assert is_pair_supported("ml", "ta") is True
    assert is_pair_supported("ta", "hi") is True
    assert is_pair_supported("ta", "invalid_code") is False
