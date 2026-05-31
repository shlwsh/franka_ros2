"""Executable Paper II synthetic closed-loop graph."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from doctor.paper2.agents.action_agent import (
    execute_followup_tool,
    execute_kg_query_tool,
    execute_resample_tool,
)
from doctor.paper2.agents.emr_fhir_agent import (
    build_emr_draft,
    build_fhir_bundle,
    repair_fhir_bundle,
)
from doctor.paper2.agents.kg_conflict_agent import compute_conflict_gate
from doctor.paper2.agents.symptom_agent import extract_symptom_entities
from doctor.paper2.agents.vision_agent import evaluate_synthetic_vision
from doctor.paper2.langgraph_router.routing import decide_route
from doctor.paper2.langgraph_router.state import Baseline, Paper2State
from doctor.paper2.tools.fhir_validator import validate_bundle


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False, sort_keys=True) + "\n")


def run_trial(
    case: dict[str, Any],
    *,
    baseline: Baseline,
    trial_id: str,
    tau_gating: float = 0.65,
    tau_vision: float = 0.55,
    max_retries: int = 1,
) -> Paper2State:
    t0 = time.perf_counter()
    timestamps = {"start": utc_now()}
    notes: list[str] = []
    tool_calls: list[dict[str, Any]] = []

    symptom_entities = extract_symptom_entities(case["symptom_text"])
    vision = evaluate_synthetic_vision(case)
    gate = compute_conflict_gate(
        symptom_entities=symptom_entities,
        expected_entities=case.get("expected_entities", []),
        vision_tags=vision["vision_tags"],
        q_img=vision["q_img"],
        tau_gating=tau_gating,
    )
    route = decide_route(gate, baseline=baseline, retry_count=0, max_retries=max_retries)

    state: Paper2State = {
        "trial_id": trial_id,
        "case_id": str(case["case_id"]),
        "baseline": baseline,
        "turn_id": 0,
        "symptom_text": str(case["symptom_text"]),
        "symptom_entities": symptom_entities,
        "image_path": vision["image_path"],
        "q_img": vision["q_img"],
        "vision_tags": vision["vision_tags"],
        "kg_matches": gate["kg_matches"],
        "gamma_conflict": gate["gamma_conflict"],
        "tau_gating": tau_gating,
        "conflict_type": str(case.get("conflict_type", "none")),
        "conflict_label": bool(case.get("conflict_label", False)),
        "route_decision": route,
        "tool_calls": tool_calls,
        "timestamps": timestamps,
        "notes": notes,
    }

    if route == "resample_vision" and baseline in ("B3", "B4"):
        updated_vision, tool_call = execute_resample_tool(vision, "go_to_tongue_pose")
        tool_calls.append(tool_call)
        vision = updated_vision
        gate = compute_conflict_gate(
            symptom_entities=symptom_entities,
            expected_entities=case.get("expected_entities", []),
            vision_tags=vision["vision_tags"],
            q_img=vision["q_img"],
            tau_gating=tau_gating,
        )
        state.update(
            {
                "q_img": vision["q_img"],
                "vision_tags": vision["vision_tags"],
                "kg_matches": gate["kg_matches"],
                "gamma_conflict": gate["gamma_conflict"],
                "turn_id": 1,
                "skill_name": "go_to_tongue_pose",
            }
        )
        route = decide_route(gate, baseline=baseline, retry_count=1, max_retries=max_retries)

    if route == "ask_followup":
        tool_calls.append(execute_followup_tool(gate["missing_entities"]))
        if baseline == "B4":
            notes.append("B4 keeps the case for human review after missing-entity follow-up.")
            route = "human_review"

    if route == "query_kg":
        tool_calls.append(execute_kg_query_tool(gate["kg_matches"]))
        route = "human_review" if baseline in ("B2", "B3", "B4") else "generate_emr"

    if route == "generate_emr":
        emr_draft = build_emr_draft(state)
        omit_observation = bool(case.get("fhir_missing")) and baseline != "B4"
        fhir_bundle = build_fhir_bundle(emr_draft, omit_observation=omit_observation)
        fhir_validation = validate_bundle(fhir_bundle)
        fhir_valid, validation_errors = fhir_validation.valid, fhir_validation.errors
        if not fhir_valid and baseline == "B4":
            tool_calls.append(
                {
                    "tool": "repair_fhir",
                    "args": {"errors": validation_errors},
                    "status": "completed",
                    "latency_ms": 6.0,
                }
            )
            fhir_bundle = repair_fhir_bundle(fhir_bundle, emr_draft)
            fhir_validation = validate_bundle(fhir_bundle)
            fhir_valid, validation_errors = fhir_validation.valid, fhir_validation.errors
        state.update(
            {
                "emr_draft": emr_draft,
                "fhir_bundle": fhir_bundle,
                "fhir_valid": fhir_valid,
                "fhir_validation_mode": fhir_validation.mode,
                "validation_errors": validation_errors,
            }
        )
    else:
        state.update({"fhir_valid": False, "validation_errors": ["not generated"]})

    predicted_conflict = state["route_decision"] != "generate_emr" or gate["gamma_conflict"] < tau_gating
    hallucination_flag = bool(case.get("conflict_label")) and route == "generate_emr"
    if baseline == "B0" and bool(case.get("conflict_label")):
        hallucination_flag = True

    timestamps["end"] = utc_now()
    state.update(
        {
            "predicted_conflict": predicted_conflict,
            "final_route_decision": route,
            "tool_calls": tool_calls,
            "hallucination_flag": hallucination_flag,
            "latency_ms": {"total": round((time.perf_counter() - t0) * 1000.0, 3)},
        }
    )
    return state
