"""
Script-Agnostic Entity Lock & Shield for TRANSLARA.
Detects, masks, and restores student names, numbers, places, and math expressions
so that the NMT engine does not mutate or mistranslate critical factual tokens.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from backend.ai.ner.gazetteer import COMMON_NAMES, COMMON_PLACES, MATH_SYMBOLS


@dataclass
class LockedEntity:
    token: str          # Masking token e.g. "⟦ENT0⟧" or "<PERSON_1>"
    text: str           # Original text e.g. "ரவி" or "5"
    type: str           # "PERSON" | "NUMBER" | "LOCATION" | "MATH" | "DATE"
    start_char: int
    end_char: int


class EntityLock:
    """
    Identifies entities that must NOT be translated literally:
    - Student/Teacher names
    - Numbers and counting digits
    - Dates and time
    - School and village names
    - Mathematical and currency expressions
    """

    # Regex patterns
    _NUM_PATTERN = re.compile(r"\b\d+(?:[\.,]\d+)?%?\b")
    _DATE_PATTERN = re.compile(r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b")
    _MATH_PATTERN = re.compile(r"\b\d+\s*[\+\-\*\/=]\s*\d+\b")
    _CURRENCY_PATTERN = re.compile(r"(?:₹|Rs\.?|\$|INR)\s*\d+(?:,\d+)*(?:\.\d+)?")

    def __init__(self):
        sorted_names = sorted(list(COMMON_NAMES), key=len, reverse=True)
        escaped_names = [re.escape(n) for n in sorted_names]
        # Robust Unicode and punctuation boundary regex
        self._names_regex = re.compile(
            rf"(?:(?<=[\s\.,!?;:\"\'\(\)\[\]])|^)({'|'.join(escaped_names)})(?=(?:[\s\.,!?;:\"\'\(\)\[\]]|$))",
            re.IGNORECASE,
        )

        sorted_places = sorted(list(COMMON_PLACES), key=len, reverse=True)
        escaped_places = [re.escape(p) for p in sorted_places]
        self._places_regex = re.compile(
            rf"(?:(?<=[\s\.,!?;:\"\'\(\)\[\]])|^)({'|'.join(escaped_places)})(?=(?:[\s\.,!?;:\"\'\(\)\[\]]|$))",
            re.IGNORECASE,
        )

    def detect_entities(self, text: str) -> List[LockedEntity]:
        """Detect all protected entities in source text."""
        entities: List[LockedEntity] = []
        occupied_spans: List[Tuple[int, int]] = []

        def _is_overlapping(start: int, end: int) -> bool:
            return any(s < end and start < e for s, e in occupied_spans)

        # 1. Detect Math & Currency
        for match in self._MATH_PATTERN.finditer(text):
            if not _is_overlapping(match.start(), match.end()):
                entities.append(LockedEntity(token="", text=match.group(), type="MATH", start_char=match.start(), end_char=match.end()))
                occupied_spans.append((match.start(), match.end()))

        for match in self._CURRENCY_PATTERN.finditer(text):
            if not _is_overlapping(match.start(), match.end()):
                entities.append(LockedEntity(token="", text=match.group(), type="CURRENCY", start_char=match.start(), end_char=match.end()))
                occupied_spans.append((match.start(), match.end()))

        # 2. Detect Dates
        for match in self._DATE_PATTERN.finditer(text):
            if not _is_overlapping(match.start(), match.end()):
                entities.append(LockedEntity(token="", text=match.group(), type="DATE", start_char=match.start(), end_char=match.end()))
                occupied_spans.append((match.start(), match.end()))

        # 3. Detect Names
        for match in self._names_regex.finditer(text):
            val = match.group(1)
            start = match.start(1)
            end = match.end(1)
            if not _is_overlapping(start, end):
                entities.append(LockedEntity(token="", text=val, type="PERSON", start_char=start, end_char=end))
                occupied_spans.append((start, end))

        # 4. Detect Places
        for match in self._places_regex.finditer(text):
            val = match.group(1)
            start = match.start(1)
            end = match.end(1)
            if not _is_overlapping(start, end):
                entities.append(LockedEntity(token="", text=val, type="LOCATION", start_char=start, end_char=end))
                occupied_spans.append((start, end))

        # 5. Detect standalone Numbers
        for match in self._NUM_PATTERN.finditer(text):
            if not _is_overlapping(match.start(), match.end()):
                entities.append(LockedEntity(token="", text=match.group(), type="NUMBER", start_char=match.start(), end_char=match.end()))
                occupied_spans.append((match.start(), match.end()))

        # Sort entities by start position
        entities.sort(key=lambda x: x.start_char)
        return entities

    def mask(self, text: str, entities: Optional[List[LockedEntity]] = None) -> Tuple[str, Dict[str, LockedEntity]]:
        """
        Replace detected entities with placeholder tokens e.g. ⟦ENT0⟧.
        Returns:
            (masked_text, token_to_entity_map)
        """
        if entities is None:
            entities = self.detect_entities(text)

        if not entities:
            return text, {}

        token_map: Dict[str, LockedEntity] = {}
        masked_parts: List[str] = []
        last_idx = 0

        for i, ent in enumerate(entities):
            token = f"⟦ENT{i}⟧"
            ent.token = token
            token_map[token] = ent

            masked_parts.append(text[last_idx:ent.start_char])
            masked_parts.append(token)
            last_idx = ent.end_char

        masked_parts.append(text[last_idx:])
        masked_text = "".join(masked_parts)
        return masked_text, token_map

    def unmask(self, translated_text: str, token_map: Dict[str, LockedEntity]) -> str:
        """
        Restore original entity text into the translated string.
        """
        if not token_map:
            return translated_text

        result = translated_text
        for token, ent in token_map.items():
            result = result.replace(token, ent.text)

            i = re.findall(r"\d+", token)[0] if re.findall(r"\d+", token) else "0"
            variations = [
                f"<ENT{i}>", f"[ENT{i}]", f"<PERSON_{i}>", f"<NUM_{i}>", f"<LOC_{i}>",
                f"⟦ENT_{i}⟧", f"⟦ent{i}⟧", f"ENT{i}", f"ENT {i}"
            ]
            for var in variations:
                result = result.replace(var, ent.text)

        return result


_entity_lock_instance: Optional[EntityLock] = None


def get_entity_lock() -> EntityLock:
    global _entity_lock_instance
    if _entity_lock_instance is None:
        _entity_lock_instance = EntityLock()
    return _entity_lock_instance
