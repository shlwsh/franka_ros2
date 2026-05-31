"""CLI for Paper II synthetic experiments."""

from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from doctor.paper2.langgraph_router.graph import run_trial, write_jsonl
from doctor.paper2.tools.dataset_loader import expand_cases

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LOG = ROOT / "experiments" / "logs" / "paper2_run_001.jsonl"
DEFAULT_RESULTS = ROOT / "experiments" / "results"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "paper2_mvp_report.md"
BASELINES = ("B0", "B1", "B2", "B3", "B4")


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _confusion(rows: list[dict[str, Any]]) -> dict[str, int]:
    tp = sum(1 for row in rows if row["conflict_label"] and row["predicted_conflict"])
    tn = sum(1 for row in rows if not row["conflict_label"] and not row["predicted_conflict"])
    fp = sum(1 for row in rows if not row["conflict_label"] and row["predicted_conflict"])
    fn = sum(1 for row in rows if row["conflict_label"] and not row["predicted_conflict"])
    return {"tp": tp, "tn": tn, "fp": fp, "fn": fn}


def _metrics(rows: list[dict[str, Any]]) -> dict[str, float]:
    cm = _confusion(rows)
    precision = _safe_div(cm["tp"], cm["tp"] + cm["fp"])
    recall = _safe_div(cm["tp"], cm["tp"] + cm["fn"])
    f1 = _safe_div(2 * precision * recall, precision + recall)
    hallucination_rate = _safe_div(sum(row["hallucination_flag"] for row in rows), len(rows))
    fhir_valid_rate = _safe_div(sum(row["fhir_valid"] for row in rows), len(rows))
    avg_latency = _safe_div(sum(row["latency_ms"]["total"] for row in rows), len(rows))
    tool_rate = _safe_div(sum(1 for row in rows if row["tool_calls"]), len(rows))
    return {
        **cm,
        "precision": precision,
        "recall": recall,
        "f1": f1,
        "hallucination_rate": hallucination_rate,
        "fhir_valid_rate": fhir_valid_rate,
        "avg_latency_ms": avg_latency,
        "tool_call_rate": tool_rate,
    }


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_results(rows: list[dict[str, Any]], results_dir: Path, report_path: Path) -> dict[str, dict[str, float]]:
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_baseline[row["baseline"]].append(row)

    summary_rows: list[dict[str, Any]] = []
    metrics_by_baseline: dict[str, dict[str, float]] = {}
    for baseline in BASELINES:
        metrics = _metrics(by_baseline[baseline])
        metrics_by_baseline[baseline] = metrics
        summary_rows.append({"baseline": baseline, **metrics})

    _write_csv(
        results_dir / "paper2_summary.csv",
        summary_rows,
        [
            "baseline",
            "tp",
            "tn",
            "fp",
            "fn",
            "precision",
            "recall",
            "f1",
            "hallucination_rate",
            "fhir_valid_rate",
            "avg_latency_ms",
            "tool_call_rate",
        ],
    )
    _write_csv(
        results_dir / "conflict_detection.csv",
        summary_rows,
        ["baseline", "precision", "recall", "f1", "tp", "tn", "fp", "fn"],
    )
    _write_csv(
        results_dir / "fhir_validation.csv",
        summary_rows,
        ["baseline", "fhir_valid_rate", "hallucination_rate"],
    )

    resample_rows = []
    for row in rows:
        resample_calls = [call for call in row["tool_calls"] if call["tool"] == "execute_skill"]
        if resample_calls:
            resample_rows.append(
                {
                    "baseline": row["baseline"],
                    "case_id": row["case_id"],
                    "q_img_after": row["q_img"],
                    "success": row["q_img"] >= 0.55,
                    "skill_name": resample_calls[0]["args"]["skill_name"],
                }
            )
    _write_csv(
        results_dir / "resample.csv",
        resample_rows,
        ["baseline", "case_id", "q_img_after", "success", "skill_name"],
    )

    _write_csv(
        results_dir / "tool_ablation.csv",
        summary_rows,
        ["baseline", "tool_call_rate", "hallucination_rate", "f1", "fhir_valid_rate"],
    )
    _write_csv(
        results_dir / "closed_loop_latency.csv",
        [
            {
                "baseline": row["baseline"],
                "trial_id": row["trial_id"],
                "case_id": row["case_id"],
                "latency_ms": row["latency_ms"]["total"],
                "tool_calls": len(row["tool_calls"]),
            }
            for row in rows
        ],
        ["baseline", "trial_id", "case_id", "latency_ms", "tool_calls"],
    )

    report_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# Paper II MVP Report",
        "",
        "Synthetic experiment; no clinical records, PHI, external LLM calls, or restricted ontology dumps.",
        "",
        "| Baseline | Conflict F1 | Hallucination Rate | FHIR Valid Rate | Tool Call Rate |",
        "|---|---:|---:|---:|---:|",
    ]
    for row in summary_rows:
        lines.append(
            f"| {row['baseline']} | {row['f1']:.4f} | {row['hallucination_rate']:.4f} | "
            f"{row['fhir_valid_rate']:.4f} | {row['tool_call_rate']:.4f} |"
        )
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return metrics_by_baseline


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--trials", type=int, default=24)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    cases = expand_cases(args.trials)
    rows: list[dict[str, Any]] = []
    for baseline in BASELINES:
        for idx, case in enumerate(cases):
            state = run_trial(case, baseline=baseline, trial_id=f"{baseline.lower()}_{idx:04d}")
            rows.append(json.loads(json.dumps(state, ensure_ascii=False)))

    write_jsonl(args.log, rows)
    metrics = write_results(rows, args.results_dir, args.report)

    print(f"wrote {len(rows)} rows to {args.log}")
    print(f"wrote results to {args.results_dir}")
    print(json.dumps(metrics, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
