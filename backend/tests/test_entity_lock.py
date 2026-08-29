"""
Unit tests for TRANSLARA Script-Agnostic Entity Lock & Numeral Shielding.
"""
import pytest
from backend.ml_engine.entity_lock import EntityLock
from backend.schemas import EntityType


def test_tamil_entity_locking():
    """TEST 7: Tamil entity locking."""
    lock = EntityLock()
    text = "அருணிடம் 5 புத்தகங்கள் உள்ளன."
    entities = lock.detect_entities(text)

    names = [e.text for e in entities if e.kind == EntityType.PERSON]
    nums = [e.text for e in entities if e.kind == EntityType.NUMBER]

    assert "அருணிடம்" in names or "அருண்" in names
    assert "5" in nums

    masked, token_map = lock.mask(text, entities)
    assert "⟦ENT" in masked
    assert "5" not in masked

    unmasked = lock.unmask(masked, token_map)
    assert "5" in unmasked


def test_telugu_entity_locking():
    """TEST 8: Telugu entity locking."""
    lock = EntityLock()
    text = "అరుణ్ దగ్గర 5 పుస్తకాలు ఉన్నాయి."
    entities = lock.detect_entities(text)

    names = [e.text for e in entities if e.kind == EntityType.PERSON]
    nums = [e.text for e in entities if e.kind == EntityType.NUMBER]

    assert "అరుణ్" in names or "అరుణ్ దగ్గర" in names
    assert "5" in nums


def test_kannada_entity_locking():
    """TEST 9: Kannada entity locking."""
    lock = EntityLock()
    text = "ಅರುಣ್ ಬಳಿ 5 ಪುಸ್ತಕಗಳಿವೆ."
    entities = lock.detect_entities(text)

    names = [e.text for e in entities if e.kind == EntityType.PERSON]
    nums = [e.text for e in entities if e.kind == EntityType.NUMBER]

    assert "ಅರುಣ್" in names or "ಅರುಣ್ ಬಳಿ" in names
    assert "5" in nums


def test_malayalam_entity_locking():
    """TEST 10: Malayalam entity locking."""
    lock = EntityLock()
    text = "അരുണിന്റെ കൈയിൽ 5 പുസ്തകങ്ങളുണ്ട്."
    entities = lock.detect_entities(text)

    names = [e.text for e in entities if e.kind == EntityType.PERSON]
    nums = [e.text for e in entities if e.kind == EntityType.NUMBER]

    assert "അരുണിന്റെ" in names or "അരുൺ" in names
    assert "5" in nums


def test_numbers_remain_unchanged():
    """TEST 11: Numbers and arithmetic expressions remain unchanged."""
    lock = EntityLock()

    # Latin, Devanagari, and Math
    text = "Students 12 and 45 + 5 = 50 in Chennai and 100."
    entities = lock.detect_entities(text)
    nums = [e.text for e in entities if e.kind == EntityType.NUMBER]

    assert any("12" in n for n in nums)
    assert any("45" in n or "50" in n for n in nums)
    assert any("100" in n for n in nums)

    # Devanagari digits
    dev_text = "कक्षा में १२ विद्यार्थी और ५ पुस्तकें हैं।"
    dev_entities = lock.detect_entities(dev_text)
    dev_nums = [e.text for e in dev_entities if e.kind == EntityType.NUMBER]
    assert "१२" in dev_nums
    assert "५" in dev_nums
