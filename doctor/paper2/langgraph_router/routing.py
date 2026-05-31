"""Routing policy for Paper II baselines."""

from __future__ import annotations

from typing import Any

from .state import Baseline, RouteDecision


def decide_route(gate: dict[str, Any], *, baseline: Baseline, retry_count: int, max_retries: int = 1) -> RouteDecision:
    if retry_count > max_retries:
        return "human_review"

    if baseline == "B0":
        return "generate_emr"

    if baseline == "B1":
        if gate["vision_quality"] < 0.55:
            return "resample_vision"
        if gate["entity_completeness"] < 1.0:
            return "ask_followup"
        return "generate_emr"

    if gate["entity_completeness"] < 1.0:
        return "ask_followup"
    if gate["vision_quality"] < 0.55:
        return "resample_vision" if baseline in ("B3", "B4") else "human_review"
    if gate["contradiction_penalty"] >= 0.5:
        return "query_kg"
    if gate["gamma_conflict"] >= gate["tau_gating"]:
        return "generate_emr"
    return "query_kg"
