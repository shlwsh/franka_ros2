"""Shared state types for Paper II closed-loop trials."""

from __future__ import annotations

from typing import Any, Literal, TypedDict

RouteDecision = Literal[
    "generate_emr",
    "resample_vision",
    "ask_followup",
    "query_kg",
    "repair_fhir",
    "human_review",
    "fail_safe",
]

Baseline = Literal["B0", "B1", "B2", "B3", "B4"]


class ToolCall(TypedDict, total=False):
    tool: str
    args: dict[str, Any]
    status: str
    latency_ms: float
    result: dict[str, Any]


class Paper2State(TypedDict, total=False):
    trial_id: str
    case_id: str
    baseline: Baseline
    turn_id: int
    symptom_text: str
    symptom_entities: list[dict[str, Any]]
    image_path: str
    q_img: float
    vision_tags: list[dict[str, Any]]
    kg_matches: list[dict[str, Any]]
    gamma_conflict: float
    tau_gating: float
    conflict_type: str
    conflict_label: bool
    predicted_conflict: bool
    route_decision: RouteDecision
    final_route_decision: RouteDecision
    tool_calls: list[ToolCall]
    skill_name: str
    robot_status: dict[str, Any]
    emr_draft: dict[str, Any]
    fhir_bundle: dict[str, Any]
    fhir_valid: bool
    fhir_validation_mode: str
    validation_errors: list[str]
    hallucination_flag: bool
    timestamps: dict[str, str]
    latency_ms: dict[str, float]
    notes: list[str]
