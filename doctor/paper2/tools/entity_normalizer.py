"""Rule-based entity normalization for Paper II synthetic evidence.

The module is intentionally small and deterministic. It centralizes the
canonical symptom/visual labels used by the MVP without introducing licensed
ontology text.
"""

from __future__ import annotations

from typing import Iterable

ENTITY_ALIASES: dict[str, tuple[str, ...]] = {
    "fever": ("fever", "发热"),
    "sore_throat": ("sore throat", "sore_throat", "咽痛"),
    "cold_aversion": ("cold aversion", "cold_aversion", "怕冷", "恶寒"),
    "mouth_bitter": ("mouth bitter", "mouth_bitter", "口苦"),
    "nausea": ("nausea", "恶心"),
    "fatigue": ("fatigue", "乏力"),
    "red_tongue": ("red tongue", "red_tongue", "舌红"),
    "pale_tongue": ("pale tongue", "pale_tongue", "舌淡"),
    "yellow_greasy_coating": (
        "yellow greasy coating",
        "yellow_greasy_coating",
        "黄腻苔",
    ),
    "thin_white_coating": ("thin white coating", "thin_white_coating", "薄白苔"),
}

_ALIAS_TO_CANONICAL = {
    alias.casefold(): canonical
    for canonical, aliases in ENTITY_ALIASES.items()
    for alias in aliases
}


def normalize_entity(value: str) -> str | None:
    """Return the canonical project-local entity label for an alias."""
    normalized = " ".join(value.replace("-", " ").replace("_", " ").split()).casefold()
    return _ALIAS_TO_CANONICAL.get(value.casefold()) or _ALIAS_TO_CANONICAL.get(normalized)


def normalize_entities(values: Iterable[str]) -> list[str]:
    """Normalize aliases while preserving first-seen order and dropping unknowns."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        canonical = normalize_entity(value)
        if canonical and canonical not in seen:
            seen.add(canonical)
            result.append(canonical)
    return result
