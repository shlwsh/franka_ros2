"""LangGraph-compatible trial state (Paper I V19)."""

from __future__ import annotations

from typing import List, TypedDict


class TrialState(TypedDict, total=False):
    trial_id: int
    image_path: str
    q_img: float
    flags: List[str]
    retry_count: int
    route_decision: str
    t_capture: str
    t_iqa: str
    t_route: str
    latency_ms: float

REQUIRED_JSONL_FIELDS = (
    'trial_id',
    'image_path',
    'q_img',
    'flags',
    'retry_count',
    'route_decision',
    't_capture',
    't_iqa',
    't_route',
    'latency_ms',
)
