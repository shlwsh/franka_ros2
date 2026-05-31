"""Build a no-PHI expert review packet and agreement report for Paper II.

The generated annotations are synthetic placeholders. They fix the columns,
rubric, and statistics that real blinded reviewers will use later, but they do
not claim that expert review has already happened.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.langgraph_router.run import BASELINES

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "experiments" / "logs" / "paper2_run_001.jsonl"
DEFAULT_PACKET = ROOT / "experiments" / "expert_review" / "review_packet.csv"
DEFAULT_ANNOTATIONS = ROOT / "experiments" / "expert_review" / "synthetic_annotations.csv"
DEFAULT_RESULTS = ROOT / "experiments" / "results" / "expert_review_agreement.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "expert_review_protocol_report.md"
DEFAULT_PROTOCOL = ROOT / "experiments" / "expert_review" / "PROTOCOL.md"

REVIEW_FIELDS = [
    "review_item_id",
    "baseline",
    "case_id",
    "conflict_label",
    "predicted_conflict",
    "final_route_decision",
    "fhir_valid",
    "hallucination_flag",
    "symptom_text",
    "vision_tags",
    "kg_matches",
    "emr_summary",
]

ANNOTATION_FIELDS = [
    "reviewer_id",
    "review_item_id",
    "factually_supported",
    "needs_human_review",
    "fhir_acceptable",
    "overall_score",
]


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def cohen_kappa(left: list[bool], right: list[bool]) -> float:
    if len(left) != len(right):
        raise ValueError("annotation vectors must have the same length")
    total = len(left)
    if total == 0:
        return 0.0
    observed = sum(1 for a, b in zip(left, right) if a == b) / total
    left_counts = Counter(left)
    right_counts = Counter(right)
    expected = sum((left_counts[label] / total) * (right_counts[label] / total) for label in (False, True))
    if expected == 1.0:
        return 1.0
    return round((observed - expected) / (1.0 - expected), 4)


def _emr_summary(row: dict[str, Any]) -> str:
    draft = row.get("emr_draft") or {}
    if not draft:
        return "not generated"
    return str(draft.get("assessment", "generated"))


def build_review_packet(rows: list[dict[str, Any]], *, max_items_per_baseline: int = 8) -> list[dict[str, Any]]:
    packet: list[dict[str, Any]] = []
    counts: dict[str, int] = defaultdict(int)
    for row in rows:
        baseline = row["baseline"]
        if baseline not in BASELINES or counts[baseline] >= max_items_per_baseline:
            continue
        counts[baseline] += 1
        packet.append(
            {
                "review_item_id": f"review_{baseline.lower()}_{counts[baseline]:03d}",
                "baseline": baseline,
                "case_id": row["case_id"],
                "conflict_label": bool(row["conflict_label"]),
                "predicted_conflict": bool(row["predicted_conflict"]),
                "final_route_decision": row["final_route_decision"],
                "fhir_valid": bool(row["fhir_valid"]),
                "hallucination_flag": bool(row["hallucination_flag"]),
                "symptom_text": row["symptom_text"],
                "vision_tags": "|".join(tag["name"] for tag in row.get("vision_tags", [])),
                "kg_matches": len(row.get("kg_matches", [])),
                "emr_summary": _emr_summary(row),
            }
        )
    return packet


def synthesize_annotations(packet: list[dict[str, Any]]) -> list[dict[str, Any]]:
    annotations: list[dict[str, Any]] = []
    for item in packet:
        supported = not bool(item["hallucination_flag"]) and (
            bool(item["fhir_valid"]) or item["final_route_decision"] == "human_review"
        )
        needs_review = bool(item["predicted_conflict"]) or item["final_route_decision"] == "human_review"
        fhir_ok = bool(item["fhir_valid"])
        for reviewer_id in ("R1_synthetic", "R2_synthetic"):
            adjusted_supported = supported
            adjusted_needs_review = needs_review
            if reviewer_id == "R2_synthetic" and item["baseline"] == "B0" and bool(item["conflict_label"]):
                adjusted_needs_review = True
            annotations.append(
                {
                    "reviewer_id": reviewer_id,
                    "review_item_id": item["review_item_id"],
                    "factually_supported": adjusted_supported,
                    "needs_human_review": adjusted_needs_review,
                    "fhir_acceptable": fhir_ok,
                    "overall_score": 4 if adjusted_supported and fhir_ok else 2,
                }
            )
    return annotations


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _agreement_rows(annotations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_reviewer: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in annotations:
        by_reviewer[row["reviewer_id"]][row["review_item_id"]] = row
    reviewers = sorted(by_reviewer)
    if len(reviewers) < 2:
        raise ValueError("at least two reviewers are required")
    left = by_reviewer[reviewers[0]]
    right = by_reviewer[reviewers[1]]
    item_ids = sorted(set(left) & set(right))
    rows: list[dict[str, Any]] = []
    for metric in ("factually_supported", "needs_human_review", "fhir_acceptable"):
        left_values = [bool(left[item_id][metric]) for item_id in item_ids]
        right_values = [bool(right[item_id][metric]) for item_id in item_ids]
        rows.append(
            {
                "metric": metric,
                "items": len(item_ids),
                "agreement_rate": _safe_div(
                    sum(1 for a, b in zip(left_values, right_values) if a == b),
                    len(item_ids),
                ),
                "cohen_kappa": cohen_kappa(left_values, right_values),
            }
        )
    return rows


def _write_protocol(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "\n".join(
            [
                "# Paper II Expert Review Protocol",
                "",
                "This protocol defines the blinded annotation packet for future real expert review.",
                "The tracked synthetic annotations are placeholders for software validation only.",
                "",
                "## Reviewer Tasks",
                "",
                "1. Mark whether the generated EMR/FHIR evidence is factually supported.",
                "2. Mark whether the case should be routed to human review.",
                "3. Mark whether the FHIR output is acceptable for structural interoperability review.",
                "4. Assign an overall 1-5 confidence score.",
                "",
                "## Safety and Data Rules",
                "",
                "- Do not include PHI or source clinical records in the packet.",
                "- Keep reviewer identities pseudonymous in analysis files.",
                "- Report Cohen kappa and agreement rate for binary fields.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def _write_report(
    report_path: Path,
    packet: list[dict[str, Any]],
    annotations: list[dict[str, Any]],
    agreement_rows: list[dict[str, Any]],
) -> None:
    lines = [
        "# Expert Review Protocol Report",
        "",
        "Synthetic protocol validation only; no real expert review has been performed.",
        "",
        f"- review packet items: {len(packet)}",
        f"- annotation rows: {len(annotations)}",
        f"- reviewers: {len({row['reviewer_id'] for row in annotations})}",
        "",
        "| Metric | Items | Agreement Rate | Cohen Kappa |",
        "|---|---:|---:|---:|",
    ]
    for row in agreement_rows:
        lines.append(
            f"| {row['metric']} | {row['items']} | {row['agreement_rate']:.4f} | "
            f"{row['cohen_kappa']:.4f} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    log_path: Path,
    packet_path: Path,
    annotations_path: Path,
    results_path: Path,
    report_path: Path,
    protocol_path: Path,
    max_items_per_baseline: int = 8,
) -> list[dict[str, Any]]:
    rows = _read_jsonl(log_path)
    packet = build_review_packet(rows, max_items_per_baseline=max_items_per_baseline)
    annotations = synthesize_annotations(packet)
    agreement_rows = _agreement_rows(annotations)
    _write_csv(packet_path, packet, REVIEW_FIELDS)
    _write_csv(annotations_path, annotations, ANNOTATION_FIELDS)
    _write_csv(results_path, agreement_rows, ["metric", "items", "agreement_rate", "cohen_kappa"])
    _write_protocol(protocol_path)
    _write_report(report_path, packet, annotations, agreement_rows)
    return agreement_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--protocol", type=Path, default=DEFAULT_PROTOCOL)
    parser.add_argument("--max-items-per-baseline", type=int, default=8)
    args = parser.parse_args()
    agreement_rows = run(
        log_path=args.log,
        packet_path=args.packet,
        annotations_path=args.annotations,
        results_path=args.results,
        report_path=args.report,
        protocol_path=args.protocol,
        max_items_per_baseline=args.max_items_per_baseline,
    )
    print(f"wrote expert review packet to {args.packet}")
    print(f"wrote expert review agreement to {args.results}")
    print(json.dumps(agreement_rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
