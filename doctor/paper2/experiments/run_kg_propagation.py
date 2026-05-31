"""Graph-propagation ablation for the Paper II KG gate.

This is not a full GNN training pipeline. It is a deterministic propagation
baseline that moves the project from a pure hand-written JSON KG toward a
traceable graph-scoring experiment.
"""

from __future__ import annotations

import argparse
import csv
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.agents.kg_conflict_agent import compute_conflict_gate, load_kg
from doctor.paper2.agents.symptom_agent import extract_symptom_entities
from doctor.paper2.agents.vision_agent import evaluate_synthetic_vision
from doctor.paper2.tools.dataset_loader import expand_cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "kg_propagation.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "kg_propagation_report.md"


def _build_signed_adjacency(kg: dict[str, Any]) -> dict[str, dict[str, float]]:
    graph: dict[str, dict[str, float]] = defaultdict(dict)
    for source, target, weight in kg.get("supports", []):
        graph[source][target] = max(graph[source].get(target, 0.0), float(weight))
    for source, target, weight in kg.get("contradicts", []):
        graph[source][target] = min(graph[source].get(target, 0.0), -float(weight))
    return graph


def propagation_score(
    symptom_entities: list[dict[str, Any]],
    vision_tags: list[dict[str, Any]],
    *,
    kg: dict[str, Any] | None = None,
    damping: float = 0.55,
) -> float:
    kg = kg or load_kg()
    graph = _build_signed_adjacency(kg)
    text_names = {str(entity["name"]) for entity in symptom_entities}
    vision_names = {str(tag["name"]) for tag in vision_tags}
    if not text_names or not vision_names:
        return 0.0

    direct = 0.0
    two_hop = 0.0
    for source in text_names:
        for middle, signed_weight in graph.get(source, {}).items():
            if middle in vision_names:
                direct += signed_weight
            for target, next_weight in graph.get(middle, {}).items():
                if target in vision_names:
                    two_hop += signed_weight * next_weight * damping

    normalizer = max(1, len(text_names) * len(vision_names))
    return round(max(-1.0, min(1.0, (direct + two_hop) / normalizer)), 4)


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _f1(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = sum(1 for row in rows if row["conflict_label"] and row["predicted_conflict"])
    tn = sum(1 for row in rows if not row["conflict_label"] and not row["predicted_conflict"])
    fp = sum(1 for row in rows if not row["conflict_label"] and row["predicted_conflict"])
    fn = sum(1 for row in rows if row["conflict_label"] and not row["predicted_conflict"])
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def run(trials: int, out_path: Path, report_path: Path, threshold: float = 0.0) -> dict[str, float]:
    rows: list[dict[str, Any]] = []
    for idx, case in enumerate(expand_cases(trials)):
        symptom_entities = extract_symptom_entities(case["symptom_text"])
        vision = evaluate_synthetic_vision(case)
        gate = compute_conflict_gate(
            symptom_entities=symptom_entities,
            expected_entities=case.get("expected_entities", []),
            vision_tags=vision["vision_tags"],
            q_img=vision["q_img"],
        )
        score = propagation_score(symptom_entities, vision["vision_tags"])
        predicted_conflict = score < threshold or gate["vision_quality"] < 0.55 or gate["entity_completeness"] < 1.0
        rows.append(
            {
                "trial_id": f"kgprop_{idx:04d}",
                "case_id": case["case_id"],
                "conflict_label": bool(case["conflict_label"]),
                "propagation_score": score,
                "gamma_conflict": gate["gamma_conflict"],
                "predicted_conflict": predicted_conflict,
                "conflict_type": case["conflict_type"],
            }
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trial_id",
                "case_id",
                "conflict_label",
                "propagation_score",
                "gamma_conflict",
                "predicted_conflict",
                "conflict_type",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    metrics = _f1(rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# KG Propagation Report",
                "",
                "Deterministic signed-edge propagation over the local KG stub.",
                "",
                f"- trials: {len(rows)}",
                f"- precision: {metrics['precision']:.4f}",
                f"- recall: {metrics['recall']:.4f}",
                f"- f1: {metrics['f1']:.4f}",
                f"- tp/fp/tn/fn: {metrics['tp']}/{metrics['fp']}/{metrics['tn']}/{metrics['fn']}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return metrics


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    metrics = run(args.trials, args.out, args.report)
    print(f"wrote KG propagation rows to {args.out}")
    print(metrics)


if __name__ == "__main__":
    main()
