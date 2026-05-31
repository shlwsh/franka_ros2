"""Trainable signed graph-attention-lite ablation for Paper II.

This remains dependency-light and small enough for CI, but unlike
``run_graph_embedding.py`` it learns edge-type weights and per-entity bias terms
from the local KG plus synthetic replay labels. It is a bridge toward the
planned GAT/GNN stage, not a substitute for large-scale neural graph training on
licensed clinical ontologies.
"""

from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.agents.kg_conflict_agent import compute_conflict_gate, load_kg
from doctor.paper2.agents.symptom_agent import extract_symptom_entities
from doctor.paper2.agents.vision_agent import evaluate_synthetic_vision
from doctor.paper2.tools.dataset_loader import expand_cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "graph_attention.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "graph_attention_report.md"


def _sigmoid(value: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-40.0, min(40.0, value))))


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


def _edge_features(
    symptom_entities: list[dict[str, Any]],
    vision_tags: list[dict[str, Any]],
    kg: dict[str, Any],
) -> dict[str, float]:
    text_names = {str(entity["name"]) for entity in symptom_entities}
    vision_names = {str(tag["name"]) for tag in vision_tags}
    support = 0.0
    contradiction = 0.0
    for source, target, weight in kg.get("supports", []):
        if source in text_names and target in vision_names:
            support += float(weight)
    for source, target, weight in kg.get("contradicts", []):
        if source in text_names and target in vision_names:
            contradiction += float(weight)
    normalizer = max(1, len(text_names) * len(vision_names))
    return {
        "support": support / normalizer,
        "contradiction": contradiction / normalizer,
    }


def _entity_hits(
    symptom_entities: list[dict[str, Any]],
    vision_tags: list[dict[str, Any]],
    entities: list[str],
) -> dict[str, float]:
    names = {str(entity["name"]) for entity in symptom_entities}
    names.update(str(tag["name"]) for tag in vision_tags)
    return {name: 1.0 if name in names else 0.0 for name in entities}


def build_training_rows(trials: int, kg: dict[str, Any] | None = None) -> list[dict[str, Any]]:
    kg = kg or load_kg()
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
        rows.append(
            {
                "trial_id": f"gat_{idx:04d}",
                "case_id": case["case_id"],
                "conflict_label": 1.0 if bool(case["conflict_label"]) else 0.0,
                "conflict_type": case["conflict_type"],
                "edge_features": _edge_features(symptom_entities, vision["vision_tags"], kg),
                "entity_hits": _entity_hits(symptom_entities, vision["vision_tags"], kg["entities"]),
                "vision_quality": gate["vision_quality"],
                "entity_completeness": gate["entity_completeness"],
                "gamma_conflict": gate["gamma_conflict"],
            }
        )
    return rows


def initialize_weights(entities: list[str]) -> dict[str, Any]:
    return {
        "bias": -0.2,
        "support_attention": -1.2,
        "contradiction_attention": 1.6,
        "low_quality_attention": 1.1,
        "missing_entity_attention": 1.1,
        "entity_bias": {name: 0.0 for name in entities},
    }


def graph_attention_score(row: dict[str, Any], weights: dict[str, Any]) -> float:
    entity_bias = sum(
        weights["entity_bias"].get(name, 0.0) * value
        for name, value in row["entity_hits"].items()
    )
    logit = (
        weights["bias"]
        + weights["support_attention"] * row["edge_features"]["support"]
        + weights["contradiction_attention"] * row["edge_features"]["contradiction"]
        + weights["low_quality_attention"] * (1.0 - row["vision_quality"])
        + weights["missing_entity_attention"] * (1.0 - row["entity_completeness"])
        + entity_bias
    )
    return round(_sigmoid(logit), 4)


def train_attention(
    rows: list[dict[str, Any]],
    entities: list[str],
    *,
    epochs: int = 160,
    learning_rate: float = 0.28,
) -> dict[str, Any]:
    weights = initialize_weights(entities)
    for _ in range(epochs):
        for row in rows:
            pred = graph_attention_score(row, weights)
            error = pred - row["conflict_label"]
            weights["bias"] -= learning_rate * error
            weights["support_attention"] -= learning_rate * error * row["edge_features"]["support"]
            weights["contradiction_attention"] -= (
                learning_rate * error * row["edge_features"]["contradiction"]
            )
            weights["low_quality_attention"] -= learning_rate * error * (1.0 - row["vision_quality"])
            weights["missing_entity_attention"] -= (
                learning_rate * error * (1.0 - row["entity_completeness"])
            )
            for name, value in row["entity_hits"].items():
                if value:
                    weights["entity_bias"][name] -= learning_rate * error * 0.08

    for key, value in list(weights.items()):
        if key == "entity_bias":
            weights[key] = {name: round(bias, 4) for name, bias in value.items()}
        else:
            weights[key] = round(value, 4)
    return weights


def run(
    trials: int,
    out_path: Path,
    report_path: Path,
    *,
    threshold: float = 0.48,
    epochs: int = 160,
) -> dict[str, Any]:
    kg = load_kg()
    training_rows = build_training_rows(trials, kg)
    weights = train_attention(training_rows, kg["entities"], epochs=epochs)
    rows: list[dict[str, Any]] = []
    for row in training_rows:
        score = graph_attention_score(row, weights)
        predicted_conflict = score >= threshold
        rows.append(
            {
                "trial_id": row["trial_id"],
                "case_id": row["case_id"],
                "conflict_label": bool(row["conflict_label"]),
                "attention_score": score,
                "predicted_conflict": predicted_conflict,
                "gamma_conflict": row["gamma_conflict"],
                "support_attention": weights["support_attention"],
                "contradiction_attention": weights["contradiction_attention"],
                "low_quality_attention": weights["low_quality_attention"],
                "missing_entity_attention": weights["missing_entity_attention"],
                "conflict_type": row["conflict_type"],
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
                "attention_score",
                "predicted_conflict",
                "gamma_conflict",
                "support_attention",
                "contradiction_attention",
                "low_quality_attention",
                "missing_entity_attention",
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
                "# Graph Attention Report",
                "",
                "Dependency-light trainable signed graph-attention-lite baseline.",
                "",
                f"- trials: {len(rows)}",
                f"- epochs: {epochs}",
                f"- threshold: {threshold:.4f}",
                f"- precision: {metrics['precision']:.4f}",
                f"- recall: {metrics['recall']:.4f}",
                f"- f1: {metrics['f1']:.4f}",
                f"- tp/fp/tn/fn: {metrics['tp']}/{metrics['fp']}/{metrics['tn']}/{metrics['fn']}",
                f"- support_attention: {weights['support_attention']:.4f}",
                f"- contradiction_attention: {weights['contradiction_attention']:.4f}",
                f"- low_quality_attention: {weights['low_quality_attention']:.4f}",
                f"- missing_entity_attention: {weights['missing_entity_attention']:.4f}",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return {"metrics": metrics, "weights": weights}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--threshold", type=float, default=0.48)
    parser.add_argument("--epochs", type=int, default=160)
    args = parser.parse_args()
    result = run(args.trials, args.out, args.report, threshold=args.threshold, epochs=args.epochs)
    print(f"wrote graph attention rows to {args.out}")
    print(result)


if __name__ == "__main__":
    main()
