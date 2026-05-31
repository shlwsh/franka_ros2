"""Knowledge-gated conflict scoring for the Paper II MVP."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .symptom_agent import entity_completeness

_KG_PATH = Path(__file__).resolve().parents[1] / "kg" / "kg_stub.json"


def load_kg(path: Path = _KG_PATH) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def score_kg_consistency(
    symptom_entities: list[dict[str, Any]],
    vision_tags: list[dict[str, Any]],
    kg: dict[str, Any] | None = None,
) -> tuple[float, float, list[dict[str, Any]]]:
    kg = kg or load_kg()
    text_names = {str(entity["name"]) for entity in symptom_entities}
    vision_names = {str(tag["name"]) for tag in vision_tags}
    matches: list[dict[str, Any]] = []
    support = 0.0
    contradiction = 0.0

    for src, dst, weight in kg.get("supports", []):
        if src in text_names and dst in vision_names:
            support = max(support, float(weight))
            matches.append({"type": "support", "source": src, "target": dst, "weight": weight})

    for src, dst, weight in kg.get("contradicts", []):
        if src in text_names and dst in vision_names:
            contradiction = max(contradiction, float(weight))
            matches.append(
                {"type": "contradiction", "source": src, "target": dst, "weight": weight}
            )

    if support == 0.0 and contradiction == 0.0:
        consistency = 0.35
    else:
        consistency = max(0.0, min(1.0, support - contradiction + 0.45))
    return round(consistency, 4), round(contradiction, 4), matches


def compute_conflict_gate(
    *,
    symptom_entities: list[dict[str, Any]],
    expected_entities: list[str],
    vision_tags: list[dict[str, Any]],
    q_img: float,
    tau_gating: float = 0.65,
) -> dict[str, Any]:
    completeness, missing = entity_completeness(symptom_entities, expected_entities)
    kg_consistency, contradiction, matches = score_kg_consistency(symptom_entities, vision_tags)
    vision_quality = max(0.0, min(1.0, q_img))
    gamma = (
        0.28 * completeness
        + 0.24 * vision_quality
        + 0.36 * kg_consistency
        - 0.22 * contradiction
    )
    gamma = max(0.0, min(1.0, gamma))
    return {
        "entity_completeness": round(completeness, 4),
        "missing_entities": missing,
        "vision_quality": round(vision_quality, 4),
        "kg_consistency": round(kg_consistency, 4),
        "contradiction_penalty": round(contradiction, 4),
        "gamma_conflict": round(gamma, 4),
        "tau_gating": tau_gating,
        "kg_matches": matches,
    }
