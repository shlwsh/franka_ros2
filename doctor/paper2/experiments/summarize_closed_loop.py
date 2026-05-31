"""Summarize Paper II closed-loop latency and route distributions."""

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

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_LATENCY = ROOT / "experiments" / "results" / "closed_loop_latency.csv"
DEFAULT_LOG = ROOT / "experiments" / "logs" / "paper2_run_001.jsonl"
DEFAULT_OUT = ROOT / "experiments" / "results" / "closed_loop_summary.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "closed_loop_summary_report.md"

FIELDNAMES = [
    "baseline",
    "trials",
    "latency_mean_ms",
    "latency_p50_ms",
    "latency_p95_ms",
    "latency_min_ms",
    "latency_max_ms",
    "tool_calls_total",
    "tool_call_rate",
    "route_distribution",
    "final_route_distribution",
]


def _safe_div(num: float, den: float) -> float:
    return round(num / den, 4) if den else 0.0


def _percentile(values: list[float], percentile: float) -> float:
    if not values:
        return 0.0
    ordered = sorted(values)
    if len(ordered) == 1:
        return round(ordered[0], 4)
    rank = (len(ordered) - 1) * percentile / 100.0
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = rank - lower
    value = ordered[lower] + (ordered[upper] - ordered[lower]) * fraction
    return round(value, 4)


def _read_latency_rows(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as f:
        rows = []
        for row in csv.DictReader(f):
            rows.append(
                {
                    "baseline": row["baseline"],
                    "trial_id": row["trial_id"],
                    "case_id": row["case_id"],
                    "latency_ms": float(row["latency_ms"]),
                    "tool_calls": int(row["tool_calls"]),
                }
            )
    return rows


def _read_route_rows(path: Path) -> dict[tuple[str, str], dict[str, str]]:
    if not path.is_file():
        return {}
    routes: dict[tuple[str, str], dict[str, str]] = {}
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            row = json.loads(line)
            key = (str(row.get("baseline", "")), str(row.get("trial_id", "")))
            routes[key] = {
                "route_decision": str(row.get("route_decision", "")),
                "final_route_decision": str(row.get("final_route_decision", "")),
            }
    return routes


def _format_distribution(counter: Counter[str], total: int) -> str:
    if not counter or total <= 0:
        return ""
    parts = []
    for name, count in sorted(counter.items()):
        if name:
            parts.append(f"{name}={count}/{total}:{_safe_div(count, total):.4f}")
    return ";".join(parts)


def _summarize_group(
    baseline: str,
    rows: list[dict[str, Any]],
    route_rows: dict[tuple[str, str], dict[str, str]],
) -> dict[str, Any]:
    latencies = [float(row["latency_ms"]) for row in rows]
    total = len(rows)
    route_counter: Counter[str] = Counter()
    final_route_counter: Counter[str] = Counter()
    for row in rows:
        route = route_rows.get((row["baseline"], row["trial_id"]), {})
        route_counter.update([route.get("route_decision", "")])
        final_route_counter.update([route.get("final_route_decision", "")])

    return {
        "baseline": baseline,
        "trials": total,
        "latency_mean_ms": _safe_div(sum(latencies), total),
        "latency_p50_ms": _percentile(latencies, 50.0),
        "latency_p95_ms": _percentile(latencies, 95.0),
        "latency_min_ms": round(min(latencies), 4) if latencies else 0.0,
        "latency_max_ms": round(max(latencies), 4) if latencies else 0.0,
        "tool_calls_total": sum(int(row["tool_calls"]) for row in rows),
        "tool_call_rate": _safe_div(sum(1 for row in rows if int(row["tool_calls"]) > 0), total),
        "route_distribution": _format_distribution(route_counter, total),
        "final_route_distribution": _format_distribution(final_route_counter, total),
    }


def summarize_closed_loop(
    latency_path: Path = DEFAULT_LATENCY,
    log_path: Path = DEFAULT_LOG,
) -> list[dict[str, Any]]:
    rows = _read_latency_rows(latency_path)
    route_rows = _read_route_rows(log_path)
    by_baseline: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in rows:
        by_baseline[row["baseline"]].append(row)

    summary_rows = [_summarize_group("ALL", rows, route_rows)]
    for baseline in sorted(by_baseline):
        summary_rows.append(_summarize_group(baseline, by_baseline[baseline], route_rows))
    return summary_rows


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def _write_report(path: Path, rows: list[dict[str, Any]], latency_path: Path, log_path: Path) -> None:
    lines = [
        "# Paper II Closed-Loop Summary Report",
        "",
        f"- latency source: {latency_path}",
        f"- route source: {log_path}",
        f"- summary rows: {len(rows)}",
        "",
        "| Baseline | Trials | Mean ms | P50 ms | P95 ms | Tool Call Rate | Final Route Distribution |",
        "|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['baseline']} | {row['trials']} | {float(row['latency_mean_ms']):.4f} | "
            f"{float(row['latency_p50_ms']):.4f} | {float(row['latency_p95_ms']):.4f} | "
            f"{float(row['tool_call_rate']):.4f} | {row['final_route_distribution']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    latency_path: Path = DEFAULT_LATENCY,
    log_path: Path = DEFAULT_LOG,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> list[dict[str, Any]]:
    rows = summarize_closed_loop(latency_path=latency_path, log_path=log_path)
    _write_csv(out_path, rows)
    _write_report(report_path, rows, latency_path, log_path)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--latency", type=Path, default=DEFAULT_LATENCY)
    parser.add_argument("--log", type=Path, default=DEFAULT_LOG)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    rows = run(
        latency_path=args.latency,
        log_path=args.log,
        out_path=args.out,
        report_path=args.report,
    )
    print(f"wrote closed-loop summary CSV to {args.out}")
    print(f"wrote closed-loop summary report to {args.report}")
    print(json.dumps(rows, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
