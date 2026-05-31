"""Rule-based symptom extraction for the Paper II MVP."""

from __future__ import annotations

from typing import Any

_LEXICON = {
    "fever": ["fever", "发热"],
    "sore_throat": ["sore throat", "咽痛"],
    "cold_aversion": ["cold aversion", "怕冷", "恶寒"],
    "mouth_bitter": ["mouth bitter", "口苦"],
    "nausea": ["nausea", "恶心"],
    "fatigue": ["fatigue", "乏力"],
}


def extract_symptom_entities(text: str) -> list[dict[str, Any]]:
    lower = text.lower()
    entities: list[dict[str, Any]] = []
    for name, aliases in _LEXICON.items():
        for alias in aliases:
            if alias.lower() in lower:
                entities.append({"name": name, "source": "text", "alias": alias})
                break
    return entities


def entity_completeness(
    entities: list[dict[str, Any]], expected_entities: list[str]
) -> tuple[float, list[str]]:
    found = {str(entity["name"]) for entity in entities}
    expected = set(expected_entities)
    if not expected:
        return 1.0, []
    missing = sorted(expected - found)
    return round((len(expected) - len(missing)) / len(expected), 4), missing


def build_followup_question(missing_entities: list[str]) -> str:
    if not missing_entities:
        return ""
    joined = ", ".join(missing_entities)
    return f"Please clarify whether the patient has the following symptoms: {joined}."
