"""Action/tool policy for Paper II MVP routing."""

from __future__ import annotations

from time import perf_counter
from typing import Any

from .symptom_agent import build_followup_question
from .vision_agent import resample_vision


def execute_resample_tool(vision_result: dict[str, Any], skill_name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    t0 = perf_counter()
    updated = resample_vision(vision_result)
    latency_ms = round((perf_counter() - t0) * 1000.0 + 18.0, 3)
    tool_call = {
        "tool": "execute_skill",
        "args": {"skill_name": skill_name},
        "status": "accepted",
        "latency_ms": latency_ms,
        "result": {"mode": "synthetic", "q_img_after": updated["q_img"]},
    }
    return updated, tool_call


def execute_followup_tool(missing_entities: list[str]) -> dict[str, Any]:
    t0 = perf_counter()
    question = build_followup_question(missing_entities)
    latency_ms = round((perf_counter() - t0) * 1000.0 + 4.0, 3)
    return {
        "tool": "ask_followup",
        "args": {"missing_entities": missing_entities},
        "status": "completed",
        "latency_ms": latency_ms,
        "result": {"question": question, "simulated_answer": "not provided in MVP"},
    }


def execute_kg_query_tool(matches: list[dict[str, Any]]) -> dict[str, Any]:
    t0 = perf_counter()
    latency_ms = round((perf_counter() - t0) * 1000.0 + 2.0, 3)
    return {
        "tool": "query_kg",
        "args": {"top_k": 5},
        "status": "completed",
        "latency_ms": latency_ms,
        "result": {"matches": matches},
    }
