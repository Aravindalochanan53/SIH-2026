"""
TRANSLARA — Script-Agnostic Entity Lock & Numeral Shielding Engine.

Protects:
- Person names (Tamil, Telugu, Kannada, Malayalam, Hindi, Santhali, etc.)
- Cities, villages, and local landmarks (Chennai, Madurai, Hyderabad, Bengaluru, Kochi, Netarhat, etc.)
- Numerals across Indian scripts (Latin 0-9, Devanagari ०-९, Tamil ௧-௯, Telugu ౦-౯, Kannada ೦-೯, Malayalam ൦-൯)
- Mathematical expressions & arithmetic equations ("5 + 3", "12 - 4")
- Curriculum and classroom identifiers
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from loguru import logger
from backend.config import settings
from backend.schemas import EntityType

# Numeral ranges across Indian scripts
# Devanagari: ०-९ (\u0966-\u096F)
# Tamil: ௧-௯ (\u0BE7-\u0BEF)
# Telugu: ౦-౯ (\u0C66-\u0C6F)
# Kannada: ೦-೯ (\u0CE6-\u0CEF)
# Malayalam: ൦-൯ (\u0D66-\u0D6F)
_INDIAN_DIGIT_CLASS = r"[0-9\u0966-\u096F\u0BE7-\u0BEF\u0C66-\u0C6F\u0CE6-\u0CEF\u0D66-\u0D6F]"

# Matches standalone numbers, decimals, and arithmetic expressions in any script
_NUMBER_RE = re.compile(
    rf"{_INDIAN_DIGIT_CLASS}+(?:[.,]{_INDIAN_DIGIT_CLASS}+)?(?:\s*[+\-×x*÷/]\s*{_INDIAN_DIGIT_CLASS}+(?:[.,]{_INDIAN_DIGIT_CLASS}+)?)*"
)

# Private-use unicode bracket template for collision-safe masking
_TOKEN_TEMPLATE = "\u27e6ENT{idx}\u27e7"  # ⟦ENT0⟧, ⟦ENT1⟧
_TOKEN_RE = re.compile(r"\u27e6ENT(\d+)\u27e7")


@dataclass
class Entity:
    text: str
    start: int
    end: int
    kind: EntityType
    phonetic_hint: Optional[str] = None


class EntityLock:
    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path(settings.data_dir) / "entities"
        self._names: set[str] = set()
        self._locations: set[str] = set()
        self._curriculum_terms: set[str] = set()
        self._phonetic_hints: dict[str, str] = {}

        self._load_seed_dictionaries()
        self._gazetteer_pattern = self._compile_gazetteer_pattern()

    def _load_seed_dictionaries(self) -> None:
        """Load pan-Indian names, cities, and curriculum entities."""
        # 1. Built-in South & North Indian Names
        built_in_names = {
            # Tamil
            "அருண்", "அருணிடம்", "பிரியா", "முருகன்", "ரவி", "லட்சுமி", "கார்த்திக்", "சுரேஷ்", "அனிதா",
            "Arun", "Priya", "Murugan", "Ravi", "Lakshmi", "Karthik", "Suresh", "Anitha",
            # Telugu
            "అరుణ్", "అరుణ్ దగ్గర", "ప్రియ", "వెంకట్", "సురేష్", "లక్ష్మి", "రవితేజ", "అనిత",
            "Venkat", "Raviteja",
            # Kannada
            "ಅರುಣ್", "ಅರುಣ್ ಬಳಿ", "ಪ್ರಿಯಾ", "ಮಂಜು", "ರವಿ", "ಸುರೇಶ್", "ಲಕ್ಷ್ಮಿ", "ಅನಿತಾ",
            "Manju",
            # Malayalam
            "അരുൺ", "അരുണിന്റെ", "പ്രിയ", "രവി", "ലക്ഷ്മി", "സുരേഷ്", "അനിത", "മനോജ്",
            "Manoj",
            # Hindi & Tribal
            "Sona Murmu", "Domon Soren", "Budhni Hembrom", "Birsa Munda", "Chunu Tudu",
            "सोना मुर्मू", "बिरसा मुंडा", "बुधनी हेम्ब्रम", "मंगल किस्कू",
        }
        self._names.update(built_in_names)

        # 2. Built-in South & North Indian Cities / Villages
        built_in_locations = {
            # Tamil Nadu
            "சென்னை", "மதுரை", "கோயம்புத்தூர்", "திருச்சி", "சேலம்", "தஞ்சாவூர்",
            "Chennai", "Madurai", "Coimbatore", "Trichy", "Salem", "Thanjavur",
            # Andhra & Telangana
            "హైదరాబాద్", "విశాఖపట్నం", "విజయవాడ", "తిరుపతి", "వరంగల్",
            "Hyderabad", "Visakhapatnam", "Vijayawada", "Tirupati", "Warangal",
            # Karnataka
            "ಬೆಂಗಳೂರು", "ಮೈಸೂರು", "ಮಂಗಳೂರು", "ಹುಬ್ಬಳ್ಳಿ", "ಬೆಳಗಾವಿ",
            "Bengaluru", "Mysuru", "Mangaluru", "Hubballi", "Belagavi",
            # Kerala
            "തിരുവനന്തപുരം", "കൊച്ചി", "കോഴിക്കോട്", "തൃശ്ശൂർ", "കണ്ണൂർ",
            "Thiruvananthapuram", "Kochi", "Kozhikode", "Thrissur", "Kannur",
            # Jharkhand & Other
            "Ranchi", "Netarhat", "Bishunpur", "Khunti", "Chaibasa", "Simdega", "Gumla",
            "राँची", "नेतरहाट", "बिशुनपुर", "खूँटी", "चाईबासा", "सिमडेगा",
        }
        self._locations.update(built_in_locations)

        # 3. Load files if present
        names_file = self.data_dir / "student_names.json"
        villages_file = self.data_dir / "villages.json"
        classroom_file = self.data_dir / "classroom_entities.json"

        if names_file.exists():
            try:
                self._names.update(json.loads(names_file.read_text(encoding="utf-8")))
            except Exception as e:
                logger.warning(f"EntityLock: Error loading {names_file}: {e}")

        if villages_file.exists():
            try:
                self._locations.update(json.loads(villages_file.read_text(encoding="utf-8")))
            except Exception as e:
                logger.warning(f"EntityLock: Error loading {villages_file}: {e}")

        if classroom_file.exists():
            try:
                cdata = json.loads(classroom_file.read_text(encoding="utf-8"))
                self._curriculum_terms.update(cdata.get("curriculum_terms", []))
                self._phonetic_hints.update(cdata.get("phonetic_hints", {}))
            except Exception as e:
                logger.warning(f"EntityLock: Error loading {classroom_file}: {e}")

        logger.info(
            f"TRANSLARA EntityLock: {len(self._names)} names, {len(self._locations)} locations tracked"
        )

    def load_roster(self, names: list[str]) -> None:
        """Add dynamic student roster list."""
        self._names.update(names)
        self._gazetteer_pattern = self._compile_gazetteer_pattern()

    def add_custom_entity(self, name: str, kind: EntityType, phonetic_hint: Optional[str] = None) -> None:
        """Register entity at runtime."""
        if kind == EntityType.PERSON:
            self._names.add(name)
        elif kind in (EntityType.VILLAGE, EntityType.LOCATION):
            self._locations.add(name)
        else:
            self._curriculum_terms.add(name)

        if phonetic_hint:
            self._phonetic_hints[name] = phonetic_hint

        self._gazetteer_pattern = self._compile_gazetteer_pattern()

    def _compile_gazetteer_pattern(self) -> re.Pattern:
        """Compile regex pattern sorted longest-first."""
        all_terms = sorted(
            self._names | self._locations | self._curriculum_terms,
            key=len,
            reverse=True,
        )
        if not all_terms:
            return re.compile(r"(?!x)x")
        escaped = [re.escape(t) for t in all_terms]
        # Unicode word boundary safe pattern
        return re.compile(r"(?:\b|_|^|\s)(" + "|".join(escaped) + r")(?:\b|_|$|\s)")

    def detect_entities(self, text: str) -> list[Entity]:
        """Detect all locked entities across South and North Indian scripts."""
        entities: list[Entity] = []
        claimed_spans: list[tuple[int, int]] = []

        def _overlaps(a_start: int, a_end: int) -> bool:
            return any(not (a_end <= s or a_start >= e) for s, e in claimed_spans)

        # 1. Numerals and Math expressions (Highest Precision)
        for m in _NUMBER_RE.finditer(text):
            matched_str = m.group().strip()
            if matched_str:
                entities.append(Entity(text=matched_str, start=m.start(), end=m.end(), kind=EntityType.NUMBER))
                claimed_spans.append((m.start(), m.end()))

        # 2. Gazetteer lookup (Proper Nouns, Names, Locations)
        for m in self._gazetteer_pattern.finditer(text):
            start, end = m.start(), m.end()
            matched = m.group(1) if m.lastindex else m.group()
            matched = matched.strip()
            if not matched or _overlaps(start, end):
                continue

            if matched in self._names:
                kind = EntityType.PERSON
            elif matched in self._locations:
                kind = EntityType.LOCATION
            else:
                kind = EntityType.CURRICULUM_TERM

            hint = self._phonetic_hints.get(matched)
            entities.append(Entity(text=matched, start=start, end=end, kind=kind, phonetic_hint=hint))
            claimed_spans.append((start, end))

        entities.sort(key=lambda e: e.start)
        return entities

    def mask(self, text: str, entities: Optional[list[Entity]] = None) -> tuple[str, dict[str, Entity]]:
        """Mask detected entities with ⟦ENT0⟧ tokens."""
        entities = entities if entities is not None else self.detect_entities(text)
        if not entities:
            return text, {}

        token_map: dict[str, Entity] = {}
        out = []
        cursor = 0
        for idx, ent in enumerate(entities):
            token = _TOKEN_TEMPLATE.format(idx=idx)
            out.append(text[cursor:ent.start])
            out.append(token)
            token_map[token] = ent
            cursor = ent.end
        out.append(text[cursor:])
        return "".join(out), token_map

    def unmask(self, translated_text: str, token_map: dict[str, Entity]) -> str:
        """Restore original entities into translated string."""
        def _replace(m: re.Match) -> str:
            token = m.group(0)
            ent = token_map.get(token)
            if ent is None:
                return token
            return ent.text

        result = _TOKEN_RE.sub(_replace, translated_text)

        # Safety-net for dropped tokens
        missing = [ent for tok, ent in token_map.items() if tok not in translated_text and ent.text not in result]
        if missing:
            logger.warning(f"Unmask safety-net: {len(missing)} dropped token(s) appended")
            result += " [" + ", ".join(e.text for e in missing) + "]"

        return result


# Singleton instance
_entity_lock_singleton: Optional[EntityLock] = None


def get_entity_lock() -> EntityLock:
    global _entity_lock_singleton
    if _entity_lock_singleton is None:
        _entity_lock_singleton = EntityLock()
    return _entity_lock_singleton
