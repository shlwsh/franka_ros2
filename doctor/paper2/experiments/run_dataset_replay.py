"""Replay Paper II baselines on a registered or file-backed case dataset."""

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

from doctor.paper2.langgraph_router.graph import run_trial, write_jsonl
from doctor.paper2.langgraph_router.run import BASELINES, write_results
from doctor.paper2.tools.dataset_loader import DEFAULT_REGISTRY_PATH, expand_loaded_cases, load_cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "dataset_replay.csv"
DEFAULT_LOG = ROOT / "experiments" / "logs" / "dataset_replay.jsonl"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "dataset_replay_report.md"
DEFAULT_RESULTS_DIR = ROOT / "experiments" / "results" / "dataset_replay"


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _write_replay_csv(rows: list[dict[str, Any]], path: Path) -> None:
    fieldnames = [
        "dataset_id",
        "baseline",
        "trial_id",
        "case_id",
        "conflict_label",
        "predicted_conflict",
        "gamma_conflict",
        "initial_route_decision",
        "final_route_decision",
        "hallucination_flag",
        "fhir_valid",
        "fhir_validation_mode",
        "tool_calls",
        "latency_ms",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "dataset_id": row.get("dataset_id", "unregistered"),
                    "baseline": row["baseline"],
                    "trial_id": row["trial_id"],
                    "case_id": row["case_id"],
                    "conflict_label": row["conflict_label"],
                    "predicted_conflict": row["predicted_conflict"],
                    "gamma_conflict": row["gamma_conflict"],
                    "initial_route_decision": row["route_decision"],
                    "final_route_decision": row["final_route_decision"],
                    "hallucination_flag": row["hallucination_flag"],
                    "fhir_valid": row["fhir_valid"],
                    "fhir_validation_mode": row.get("fhir_validation_mode", ""),
                    "tool_calls": len(row["tool_calls"]),
                    "latency_ms": row["latency_ms"]["total"],
                }
            )


def _summarize_dataset(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_baseline[row["baseline"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    for baseline in BASELINES:
        baseline_rows = by_baseline[baseline]
        if not baseline_rows:
            continue
        tp = sum(1 for row in baseline_rows if row["conflict_label"] and row["predicted_conflict"])
        fp = sum(1 for row in baseline_rows if not row["conflict_label"] and row["predicted_conflict"])
        fn = sum(1 for row in baseline_rows if row["conflict_label"] and not row["predicted_conflict"])
        precision = _safe_div(tp, tp + fp)
        recall = _safe_div(tp, tp + fn)
        f1 = _safe_div(2 * precision * recall, precision + recall)
        summary_rows.append(
            {
                "baseline": baseline,
                "cases": len(baseline_rows),
                "precision": precision,
                "recall": recall,
                "f1": f1,
                "hallucination_rate": _safe_div(
                    sum(row["hallucination_flag"] for row in baseline_rows), len(baseline_rows)
                ),
                "fhir_valid_rate": _safe_div(
                    sum(row["fhir_valid"] for row in baseline_rows), len(baseline_rows)
                ),
                "tool_call_rate": _safe_div(
                    sum(1 for row in baseline_rows if row["tool_calls"]), len(baseline_rows)
                ),
            }
        )
    return summary_rows


def _write_report(
    *,
    report_path: Path,
    dataset_label: str,
    source_label: str,
    cases: list[dict[str, Any]],
    rows: list[dict[str, Any]],
    summary_rows: list[dict[str, Any]],
) -> None:
    access_levels = sorted({str(case.get("dataset_access_level", "unregistered")) for case in cases})
    licenses = sorted({str(case.get("dataset_license", "unspecified")) for case in cases})
    lines = [
        "# Dataset Replay Report",
        "",
        f"- dataset: {dataset_label}",
        f"- source: {source_label}",
        f"- unique cases: {len(cases)}",
        f"- replay rows: {len(rows)}",
        f"- access levels: {', '.join(access_levels)}",
        f"- licenses: {'; '.join(licenses)}",
        "",
        "| Baseline | Cases | F1 | Hallucination Rate | FHIR Valid Rate | Tool Call Rate |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['baseline']} | {row['cases']} | {row['f1']:.4f} | "
            f"{row['hallucination_rate']:.4f} | {row['fhir_valid_rate']:.4f} | "
            f"{row['tool_call_rate']:.4f} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    trials: int,
    out_path: Path,
    log_path: Path,
    report_path: Path,
    results_dir: Path,
    dataset_id: str | None = None,
    source: Path | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    allow_controlled: bool = False,
) -> list[dict[str, Any]]:
    cases = load_cases(
        source=source,
        dataset_id=dataset_id,
        registry_path=registry_path,
        allow_controlled=allow_controlled,
    )
    replay_cases = expand_loaded_cases(cases, trials)
    dataset_label = dataset_id or str(source or "unregistered")
    source_label = str(source or registry_path)

    rows: list[dict[str, Any]] = []
    for baseline in BASELINES:
        for idx, case in enumerate(replay_cases):
            state = run_trial(case, baseline=baseline, trial_id=f"{baseline.lower()}_data_{idx:04d}")
            row = json.loads(json.dumps(state, ensure_ascii=False))
            row["dataset_id"] = case.get("dataset_id", dataset_label)
            rows.append(row)

    write_jsonl(log_path, rows)
    _write_replay_csv(rows, out_path)
    write_results(rows, results_dir, results_dir / "paper2_mvp_report.md")
    summary_rows = _summarize_dataset(rows)
    _write_report(
        report_path=report_path,
        dataset_label=dataset_label,
        source_label=source_label,
        cases=cases,
        rows=rows,
        summary_rows=summary_rows,
    )
    return summary_rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--dataset-id", default="sample_open_csv")
    parser.add_argument("--source", type=Path)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--allow-controlled", action="store_true")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    args = parser.parse_args()

    summary_rows = run(
        trials=args.trials,
        out_path=args.out,
        log_path=args.log,
        report_path=args.report,
        results_dir=args.results_dir,
        dataset_id=args.dataset_id if args.source is None else None,
        source=args.source,
        registry_path=args.registry,
        allow_controlled=args.allow_controlled,
    )
    print(f"wrote dataset replay rows to {args.out}")
    print(f"wrote dataset replay report to {args.report}")
    print(json.dumps(summary_rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
