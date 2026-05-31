import csv
import json
from pathlib import Path

from doctor.paper2.experiments.summarize_closed_loop import run, summarize_closed_loop


def _write_latency(path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["baseline", "trial_id", "case_id", "latency_ms", "tool_calls"],
        )
        writer.writeheader()
        writer.writerows(
            [
                {"baseline": "B0", "trial_id": "b0_0000", "case_id": "c1", "latency_ms": "10", "tool_calls": "0"},
                {"baseline": "B0", "trial_id": "b0_0001", "case_id": "c2", "latency_ms": "20", "tool_calls": "1"},
                {"baseline": "B1", "trial_id": "b1_0000", "case_id": "c1", "latency_ms": "30", "tool_calls": "1"},
                {"baseline": "B1", "trial_id": "b1_0001", "case_id": "c2", "latency_ms": "40", "tool_calls": "0"},
            ]
        )


def _write_log(path: Path) -> None:
    rows = [
        {"baseline": "B0", "trial_id": "b0_0000", "route_decision": "generate_emr", "final_route_decision": "generate_emr"},
        {"baseline": "B0", "trial_id": "b0_0001", "route_decision": "resample_vision", "final_route_decision": "generate_emr"},
        {"baseline": "B1", "trial_id": "b1_0000", "route_decision": "query_kg", "final_route_decision": "generate_emr"},
        {"baseline": "B1", "trial_id": "b1_0001", "route_decision": "query_kg", "final_route_decision": "human_review"},
    ]
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row) + "\n")


def test_summarize_closed_loop_reports_percentiles_and_routes(tmp_path: Path):
    latency = tmp_path / "closed_loop_latency.csv"
    log = tmp_path / "paper2_run_001.jsonl"
    _write_latency(latency)
    _write_log(log)

    rows = summarize_closed_loop(latency_path=latency, log_path=log)
    by_baseline = {row["baseline"]: row for row in rows}

    assert by_baseline["B0"]["latency_p50_ms"] == 15.0
    assert by_baseline["B0"]["latency_p95_ms"] == 19.5
    assert by_baseline["B0"]["tool_call_rate"] == 0.5
    assert "resample_vision" in by_baseline["B0"]["route_distribution"]
    assert by_baseline["ALL"]["trials"] == 4


def test_closed_loop_summary_run_writes_csv_and_report(tmp_path: Path):
    latency = tmp_path / "closed_loop_latency.csv"
    log = tmp_path / "paper2_run_001.jsonl"
    out = tmp_path / "closed_loop_summary.csv"
    report = tmp_path / "closed_loop_summary_report.md"
    _write_latency(latency)
    _write_log(log)

    rows = run(latency_path=latency, log_path=log, out_path=out, report_path=report)

    assert out.is_file()
    assert report.is_file()
    assert len(rows) == 3
    assert "P95 ms" in report.read_text(encoding="utf-8")
