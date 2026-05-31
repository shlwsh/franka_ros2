"""Vision agent for synthetic and optional API-backed image evaluation."""

from __future__ import annotations

from typing import Any


def evaluate_synthetic_vision(case: dict[str, Any]) -> dict[str, Any]:
    q_img = float(case["q_img"])
    flags: list[str] = []
    if q_img < 0.5:
        flags.append("low_quality")
    if q_img < 0.45:
        flags.append("blur")
    if case.get("conflict_type") == "vision_low_quality":
        flags.append("occlusion")

    return {
        "q_img": round(q_img, 4),
        "flags": sorted(set(flags)),
        "vision_tags": [
            {"name": tag, "score": round(max(0.45, min(0.95, q_img)), 4)}
            for tag in case.get("vision_tags", [])
        ],
        "roi_quality": round(q_img, 4),
        "image_path": f"synthetic/{case['case_id']}.png",
    }


def resample_vision(previous: dict[str, Any]) -> dict[str, Any]:
    """Simulate a successful embodied resample with bounded improvement."""
    improved = dict(previous)
    q_img = min(0.92, float(previous.get("q_img", 0.0)) + 0.34)
    improved["q_img"] = round(q_img, 4)
    improved["roi_quality"] = round(q_img, 4)
    improved["flags"] = []
    improved["resampled"] = True
    improved["vision_tags"] = [
        {**tag, "score": round(max(float(tag.get("score", 0.5)), q_img), 4)}
        for tag in previous.get("vision_tags", [])
    ]
    return improved
