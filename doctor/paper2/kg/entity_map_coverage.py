"""Validate Paper II entity mapping coverage without restricted ontology dumps."""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_KG = ROOT / "kg" / "kg_stub.json"
DEFAULT_MAP = ROOT / "kg" / "entity_map.csv"
DEFAULT_OUT = ROOT / "experiments" / "results" / "entity_map_coverage.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "entity_map_coverage_report.md"
REQUIRED_FIELDS = {
    "entity",
    "category",
    "local_code",
    "fhir_target",
    "icd11_stub",
    "snomed_stub",
    "license_status",
    "mapping_basis",
}


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _load_kg_entities(path: Path) -> set[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return {str(item) for item in payload.get("entities", [])}


def _load_map(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_FIELDS - set(reader.fieldnames or [])
        if missing:
            raise ValueError(f"entity map missing fields: {', '.join(sorted(missing))}")
        return [dict(row) for row in reader]


def coverage_rows(kg_path: Path = DEFAULT_KG, map_path: Path = DEFAULT_MAP) -> list[dict[str, Any]]:
    kg_entities = _load_kg_entities(kg_path)
    mapping = _load_map(map_path)
    mapped_entities = {row["entity"] for row in mapping}
    rows: list[dict[str, Any]] = []
    for entity in sorted(kg_entities):
        row = next((item for item in mapping if item["entity"] == entity), None)
        rows.append(
            {
                "entity": entity,
                "mapped": row is not None,
                "category": row["category"] if row else "",
                "fhir_target": row["fhir_target"] if row else "",
                "license_status": row["license_status"] if row else "missing",
            }
        )
    for entity in sorted(mapped_entities - kg_entities):
        rows.append(
            {
                "entity": entity,
                "mapped": False,
                "category": "extra_mapping",
                "fhir_target": "",
                "license_status": "not-in-kg",
            }
        )
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    kg_rows = [row for row in rows if row["category"] != "extra_mapping"]
    mapped = sum(1 for row in kg_rows if row["mapped"])
    fhir_mapped = sum(1 for row in kg_rows if row["fhir_target"])
    placeholders = sum(1 for row in kg_rows if row["license_status"] == "placeholder-only")
    return {
        "kg_entities": len(kg_rows),
        "mapped_entities": mapped,
        "coverage": _safe_div(mapped, len(kg_rows)),
        "fhir_target_coverage": _safe_div(fhir_mapped, len(kg_rows)),
        "placeholder_only": placeholders,
        "extra_mappings": sum(1 for row in rows if row["category"] == "extra_mapping"),
    }


def write_outputs(rows: list[dict[str, Any]], out_path: Path, report_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["entity", "mapped", "category", "fhir_target", "license_status"],
        )
        writer.writeheader()
        writer.writerows(rows)

    summary = summarize(rows)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(
        "\n".join(
            [
                "# Entity Map Coverage Report",
                "",
                "License-safe coverage report for the Paper II KG entity map.",
                "",
                f"- kg_entities: {summary['kg_entities']}",
                f"- mapped_entities: {summary['mapped_entities']}",
                f"- coverage: {summary['coverage']:.4f}",
                f"- fhir_target_coverage: {summary['fhir_target_coverage']:.4f}",
                f"- placeholder_only: {summary['placeholder_only']}",
                f"- extra_mappings: {summary['extra_mappings']}",
                "",
                "No restricted ICD/SNOMED/UMLS ontology dump is included.",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return summary


def run(
    kg_path: Path = DEFAULT_KG,
    map_path: Path = DEFAULT_MAP,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    rows = coverage_rows(kg_path, map_path)
    return write_outputs(rows, out_path, report_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--kg", type=Path, default=DEFAULT_KG)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = run(args.kg, args.map, args.out, args.report)
    print(f"wrote entity map coverage to {args.out}")
    print(summary)


if __name__ == "__main__":
    main()
