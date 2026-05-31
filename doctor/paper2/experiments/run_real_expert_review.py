"""Validate real expert-review annotations for Paper II.

This script does not synthesize reviewer labels. It consumes a completed
real-annotation CSV, checks it against the generated review packet, computes
agreement statistics, and writes auditable evidence only when the file passes
minimum real-review criteria.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.experiments.run_expert_review import (
    ANNOTATION_FIELDS,
    cohen_kappa,
)

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_PACKET = ROOT / "experiments" / "expert_review" / "review_packet.csv"
DEFAULT_ANNOTATIONS = ROOT / "experiments" / "expert_review" / "real_annotations.csv"
DEFAULT_TEMPLATE = ROOT / "experiments" / "expert_review" / "real_annotations.template.csv"
DEFAULT_RESULTS = ROOT / "experiments" / "results" / "real_expert_review_agreement.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "real_expert_review_report.md"
BOOL_FIELDS = ("factually_supported", "needs_human_review", "fhir_acceptable")


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def _parse_bool(value: Any, *, field: str, row_id: str) -> bool:
    text = str(value).strip().lower()
    if text in {"true", "1", "yes", "y"}:
        return True
    if text in {"false", "0", "no", "n"}:
        return False
    raise ValueError(f"{row_id}: {field} must be true/false-like")


def _parse_score(value: Any, *, row_id: str) -> int:
    try:
        score = int(str(value).strip())
    except ValueError as exc:
        raise ValueError(f"{row_id}: overall_score must be an integer") from exc
    if score < 1 or score > 5:
        raise ValueError(f"{row_id}: overall_score must be in [1, 5]")
    return score


def write_annotation_template(packet_path: Path = DEFAULT_PACKET, template_path: Path = DEFAULT_TEMPLATE) -> None:
    packet = _read_csv(packet_path)
    template_path.parent.mkdir(parents=True, exist_ok=True)
    with template_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "reviewer_id",
            "review_item_id",
            "factually_supported",
            "needs_human_review",
            "fhir_acceptable",
            "overall_score",
            "reviewer_comment",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for item in packet:
            writer.writerow(
                {
                    "reviewer_id": "",
                    "review_item_id": item["review_item_id"],
                    "factually_supported": "",
                    "needs_human_review": "",
                    "fhir_acceptable": "",
                    "overall_score": "",
                    "reviewer_comment": "",
                }
            )


def load_and_validate_annotations(
    *,
    packet_path: Path = DEFAULT_PACKET,
    annotations_path: Path = DEFAULT_ANNOTATIONS,
    min_reviewers: int = 2,
    require_full_overlap: bool = True,
) -> list[dict[str, Any]]:
    if not packet_path.is_file():
        raise FileNotFoundError(f"review packet not found: {packet_path}")
    if not annotations_path.is_file():
        raise FileNotFoundError(f"real annotation CSV not found: {annotations_path}")

    packet_rows = _read_csv(packet_path)
    packet_ids = {row["review_item_id"] for row in packet_rows}
    if not packet_ids:
        raise ValueError("review packet has no items")

    raw_rows = _read_csv(annotations_path)
    if not raw_rows:
        raise ValueError("real annotation CSV is empty")
    missing_columns = set(ANNOTATION_FIELDS) - set(raw_rows[0])
    if missing_columns:
        raise ValueError(f"real annotation CSV missing fields: {', '.join(sorted(missing_columns))}")

    normalized: list[dict[str, Any]] = []
    seen_pairs: set[tuple[str, str]] = set()
    for idx, row in enumerate(raw_rows, start=2):
        row_id = f"{annotations_path}:{idx}"
        reviewer_id = str(row.get("reviewer_id", "")).strip()
        item_id = str(row.get("review_item_id", "")).strip()
        if not reviewer_id:
            raise ValueError(f"{row_id}: reviewer_id is required")
        if "synthetic" in reviewer_id.lower():
            raise ValueError(f"{row_id}: reviewer_id must not be synthetic")
        if item_id not in packet_ids:
            raise ValueError(f"{row_id}: review_item_id is not in review packet: {item_id}")
        pair = (reviewer_id, item_id)
        if pair in seen_pairs:
            raise ValueError(f"{row_id}: duplicate reviewer/item annotation: {reviewer_id}/{item_id}")
        seen_pairs.add(pair)
        normalized.append(
            {
                "reviewer_id": reviewer_id,
                "review_item_id": item_id,
                "factually_supported": _parse_bool(
                    row.get("factually_supported"), field="factually_supported", row_id=row_id
                ),
                "needs_human_review": _parse_bool(
                    row.get("needs_human_review"), field="needs_human_review", row_id=row_id
                ),
                "fhir_acceptable": _parse_bool(
                    row.get("fhir_acceptable"), field="fhir_acceptable", row_id=row_id
                ),
                "overall_score": _parse_score(row.get("overall_score"), row_id=row_id),
            }
        )

    reviewers = sorted({row["reviewer_id"] for row in normalized})
    if len(reviewers) < min_reviewers:
        raise ValueError(f"at least {min_reviewers} real reviewers are required")

    by_item: dict[str, set[str]] = defaultdict(set)
    for row in normalized:
        by_item[row["review_item_id"]].add(row["reviewer_id"])
    under_reviewed = sorted(item_id for item_id, reviewers_for_item in by_item.items() if len(reviewers_for_item) < 2)
    if under_reviewed:
        raise ValueError(f"items with fewer than two reviewers: {', '.join(under_reviewed[:10])}")
    missing_items = sorted(packet_ids - set(by_item))
    if require_full_overlap and missing_items:
        raise ValueError(f"packet items without real annotations: {', '.join(missing_items[:10])}")
    return normalized


def agreement_rows(annotations: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_reviewer: dict[str, dict[str, dict[str, Any]]] = defaultdict(dict)
    for row in annotations:
        by_reviewer[row["reviewer_id"]][row["review_item_id"]] = row
    reviewers = sorted(by_reviewer)
    if len(reviewers) < 2:
        raise ValueError("at least two reviewers are required")

    item_ids = sorted(set.intersection(*(set(by_reviewer[reviewer]) for reviewer in reviewers)))
    if not item_ids:
        raise ValueError("no overlapping review items across reviewers")

    rows: list[dict[str, Any]] = []
    left = by_reviewer[reviewers[0]]
    right = by_reviewer[reviewers[1]]
    for metric in BOOL_FIELDS:
        left_values = [bool(left[item_id][metric]) for item_id in item_ids]
        right_values = [bool(right[item_id][metric]) for item_id in item_ids]
        agreement = sum(1 for a, b in zip(left_values, right_values) if a == b) / len(item_ids)
        rows.append(
            {
                "metric": metric,
                "items": len(item_ids),
                "reviewers": len(reviewers),
                "agreement_rate": round(agreement, 4),
                "cohen_kappa": cohen_kappa(left_values, right_values),
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["metric", "items", "reviewers", "agreement_rate", "cohen_kappa"]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _write_report(
    report_path: Path,
    *,
    packet_path: Path,
    annotations_path: Path,
    annotations: list[dict[str, Any]],
    rows: list[dict[str, Any]],
) -> None:
    reviewers = sorted({row["reviewer_id"] for row in annotations})
    item_ids = sorted({row["review_item_id"] for row in annotations})
    lines = [
        "# Real Expert Review Report",
        "",
        "Validation and agreement statistics for real Paper II expert annotations.",
        "",
        f"- review packet: {packet_path}",
        f"- real annotations: {annotations_path}",
        f"- reviewers: {len(reviewers)}",
        f"- annotated items: {len(item_ids)}",
        f"- annotation rows: {len(annotations)}",
        "",
        "| Metric | Items | Reviewers | Agreement Rate | Cohen Kappa |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in rows:
        lines.append(
            f"| {row['metric']} | {row['items']} | {row['reviewers']} | "
            f"{row['agreement_rate']:.4f} | {row['cohen_kappa']:.4f} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    packet_path: Path = DEFAULT_PACKET,
    annotations_path: Path = DEFAULT_ANNOTATIONS,
    results_path: Path = DEFAULT_RESULTS,
    report_path: Path = DEFAULT_REPORT,
    min_reviewers: int = 2,
    require_full_overlap: bool = True,
) -> list[dict[str, Any]]:
    annotations = load_and_validate_annotations(
        packet_path=packet_path,
        annotations_path=annotations_path,
        min_reviewers=min_reviewers,
        require_full_overlap=require_full_overlap,
    )
    rows = agreement_rows(annotations)
    _write_csv(results_path, rows)
    _write_report(
        report_path,
        packet_path=packet_path,
        annotations_path=annotations_path,
        annotations=annotations,
        rows=rows,
    )
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", type=Path, default=DEFAULT_PACKET)
    parser.add_argument("--annotations", type=Path, default=DEFAULT_ANNOTATIONS)
    parser.add_argument("--results", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--min-reviewers", type=int, default=2)
    parser.add_argument("--allow-partial-overlap", action="store_true")
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    args = parser.parse_args()

    if args.write_template:
        write_annotation_template(args.packet, args.template)
        print(f"wrote real annotation template to {args.template}")
        return

    rows = run(
        packet_path=args.packet,
        annotations_path=args.annotations,
        results_path=args.results,
        report_path=args.report,
        min_reviewers=args.min_reviewers,
        require_full_overlap=not args.allow_partial_overlap,
    )
    print(f"wrote real expert review agreement to {args.results}")
    print(f"wrote real expert review report to {args.report}")
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
