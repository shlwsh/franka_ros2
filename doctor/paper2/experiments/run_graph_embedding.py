"""Deterministic message-passing embedding ablation for Paper II.

This script is a dependency-light bridge toward the planned GNN/GAT stage. It
does not train neural weights. Instead, it initializes each KG node with a
one-hot vector and performs signed message passing over support/contradiction
edges. Text-vision compatibility is then scored by cosine similarity between the
pooled text and vision embeddings.
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
DEFAULT_OUT = ROOT / "experiments" / "results" / "graph_embedding.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "graph_embedding_report.md"


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(a: list[float]) -> float:
    return math.sqrt(sum(x * x for x in a))


def _cosine(a: list[float], b: list[float]) -> float:
    den = _norm(a) * _norm(b)
    return round(_dot(a, b) / den, 4) if den else 0.0


def _add(a: list[float], b: list[float], scale: float = 1.0) -> list[float]:
    return [x + scale * y for x, y in zip(a, b)]


def _pool(names: set[str], embeddings: dict[str, list[float]]) -> list[float]:
    if not names:
        return [0.0 for _ in next(iter(embeddings.values()))]
    pooled = [0.0 for _ in next(iter(embeddings.values()))]
    for name in names:
        pooled = _add(pooled, embeddings.get(name, [0.0 for _ in pooled]))
    return [value / len(names) for value in pooled]


def build_embeddings(kg: dict[str, Any], *, steps: int = 2, damping: float = 0.45) -> dict[str, list[float]]:
    entities = list(kg["entities"])
    index = {name: idx for idx, name in enumerate(entities)}
    embeddings = {
        name: [1.0 if idx == index[name] else 0.0 for idx in range(len(entities))]
        for name in entities
    }
    edges: list[tuple[str, str, float]] = []
    for source, target, weight in kg.get("supports", []):
        edges.append((source, target, float(weight)))
    for source, target, weight in kg.get("contradicts", []):
        edges.append((source, target, -float(weight)))

    for _ in range(steps):
        updated = {name: list(vector) for name, vector in embeddings.items()}
        for source, target, signed_weight in edges:
            message = embeddings[source]
            updated[target] = _add(updated[target], message, damping * signed_weight)
            updated[source] = _add(updated[source], embeddings[target], damping * signed_weight)
        embeddings = updated
    return embeddings


def embedding_score(
    symptom_entities: list[dict[str, Any]],
    vision_tags: list[dict[str, Any]],
    *,
    kg: dict[str, Any] | None = None,
    embeddings: dict[str, list[float]] | None = None,
) -> float:
    kg = kg or load_kg()
    embeddings = embeddings or build_embeddings(kg)
    text_names = {str(entity["name"]) for entity in symptom_entities}
    vision_names = {str(tag["name"]) for tag in vision_tags}
    text_vec = _pool(text_names, embeddings)
    vision_vec = _pool(vision_names, embeddings)
    return _cosine(text_vec, vision_vec)


def _f1(rows: list[dict[str, Any]]) -> dict[str, float]:
    tp = sum(1 for row in rows if row["conflict_label"] and row["predicted_conflict"])
    tn = sum(1 for row in rows if not row["conflict_label"] and not row["predicted_conflict"])
    fp = sum(1 for row in rows if not row["conflict_label"] and row["predicted_conflict"])
    fn = sum(1 for row in rows if row["conflict_label"] and not row["predicted_conflict"])
    precision = _safe_div(tp, tp + fp)
    recall = _safe_div(tp, tp + fn)
    f1 = _safe_div(2 * precision * recall, precision + recall)
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn, "precision": precision, "recall": recall, "f1": f1}


def run(trials: int, out_path: Path, report_path: Path, threshold: float = 0.18) -> dict[str, float]:
    kg = load_kg()
    embeddings = build_embeddings(kg)
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
        score = embedding_score(symptom_entities, vision["vision_tags"], kg=kg, embeddings=embeddings)
        predicted_conflict = score < threshold or gate["vision_quality"] < 0.55 or gate["entity_completeness"] < 1.0
        rows.append(
            {
                "trial_id": f"embed_{idx:04d}",
                "case_id": case["case_id"],
                "conflict_label": bool(case["conflict_label"]),
                "embedding_score": score,
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
                "embedding_score",
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
                "# Graph Embedding Report",
                "",
                "Deterministic signed message-passing embedding over the local KG stub.",
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
    print(f"wrote graph embedding rows to {args.out}")
    print(metrics)


if __name__ == "__main__":
    main()
