"""Batch replay FHIR validation over Paper II generated Bundles.

The script exports each generated Bundle as JSON and validates it with the
project adapter. By default this is the local deterministic structural checker.
When ``PAPER2_FHIR_VALIDATOR_CMD`` is set, the same replay records whether the
external validator passed or fell back to local diagnostics.
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

from doctor.paper2.agents.emr_fhir_agent import build_emr_draft, build_fhir_bundle
from doctor.paper2.langgraph_router.run import BASELINES
from doctor.paper2.tools.dataset_loader import expand_cases
from doctor.paper2.tools.fhir_validator import validate_bundle

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "fhir_validator_replay.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "fhir_validator_replay_report.md"
DEFAULT_BUNDLE_DIR = ROOT / "experiments" / "fhir_bundles"


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _state_from_case(case: dict[str, Any]) -> dict[str, Any]:
    return {
        "case_id": case["case_id"],
        "symptom_text": case["symptom_text"],
        "symptom_entities": [{"name": item} for item in case.get("expected_entities", [])],
        "vision_tags": [{"name": item, "score": case["q_img"]} for item in case.get("vision_tags", [])],
        "kg_matches": [],
    }


def _write_bundle(path: Path, bundle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _display_path(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    fieldnames = [
        "baseline",
        "trial_id",
        "case_id",
        "bundle_path",
        "omit_observation",
        "valid",
        "mode",
        "error_count",
        "errors",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _summary(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_baseline[row["baseline"]].append(row)
    summary_rows: list[dict[str, Any]] = []
    for baseline in BASELINES:
        baseline_rows = by_baseline[baseline]
        if not baseline_rows:
            continue
        summary_rows.append(
            {
                "baseline": baseline,
                "bundles": len(baseline_rows),
                "valid_rate": _safe_div(sum(row["valid"] for row in baseline_rows), len(baseline_rows)),
                "invalid_rate": _safe_div(
                    sum(1 for row in baseline_rows if not row["valid"]), len(baseline_rows)
                ),
                "modes": ", ".join(sorted({str(row["mode"]) for row in baseline_rows})),
            }
        )
    return summary_rows


def _write_report(report_path: Path, rows: list[dict[str, Any]]) -> None:
    summary_rows = _summary(rows)
    lines = [
        "# FHIR Validator Replay Report",
        "",
        "Batch validation of generated Paper II Bundle JSON artifacts.",
        "",
        "| Baseline | Bundles | Valid Rate | Invalid Rate | Modes |",
        "|---|---:|---:|---:|---|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['baseline']} | {row['bundles']} | {row['valid_rate']:.4f} | "
            f"{row['invalid_rate']:.4f} | {row['modes']} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    trials: int,
    out_path: Path,
    report_path: Path,
    bundle_dir: Path,
    include_invalid: bool = True,
) -> list[dict[str, Any]]:
    cases = expand_cases(trials)
    rows: list[dict[str, Any]] = []
    for baseline in BASELINES:
        for idx, case in enumerate(cases):
            trial_id = f"{baseline.lower()}_fhir_{idx:04d}"
            emr_draft = build_emr_draft(_state_from_case(case))
            omit_observation = include_invalid and bool(case.get("fhir_missing")) and baseline != "B4"
            bundle = build_fhir_bundle(emr_draft, omit_observation=omit_observation)
            bundle_path = bundle_dir / baseline / f"{trial_id}.json"
            _write_bundle(bundle_path, bundle)
            result = validate_bundle(bundle)
            rows.append(
                {
                    "baseline": baseline,
                    "trial_id": trial_id,
                    "case_id": case["case_id"],
                    "bundle_path": _display_path(bundle_path),
                    "omit_observation": omit_observation,
                    "valid": result.valid,
                    "mode": result.mode,
                    "error_count": len(result.errors),
                    "errors": "; ".join(result.errors),
                }
            )

    _write_csv(out_path, rows)
    _write_report(report_path, rows)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--no-invalid", action="store_true")
    args = parser.parse_args()
    rows = run(
        trials=args.trials,
        out_path=args.out,
        report_path=args.report,
        bundle_dir=args.bundle_dir,
        include_invalid=not args.no_invalid,
    )
    print(f"wrote {len(rows)} FHIR validation rows to {args.out}")
    print(f"wrote FHIR validation report to {args.report}")


if __name__ == "__main__":
    main()
