import csv
from pathlib import Path

from doctor.paper2.experiments.run_phase_completion_audit import (
    STATUS_BLOCKED,
    STATUS_PARTIAL,
    STATUS_READY,
    build_rows,
    run,
    validate_phase_completion_audit_csv,
)
from doctor.paper2.experiments.run_readiness_audit import build_audit


def test_phase_completion_audit_maps_all_planned_tasks():
    rows = build_rows()
    task_ids = {row["task_id"] for row in rows}

    assert len(rows) == 35
    assert {"P2-0-1", "P2-1-4", "P2-4-3", "P2-6-5"} <= task_ids
    assert {row["status"] for row in rows} <= {STATUS_READY, STATUS_PARTIAL, STATUS_BLOCKED}
    assert any(row["status"] == STATUS_BLOCKED for row in rows)


def test_phase_completion_run_writes_csv_and_report(tmp_path: Path):
    out = tmp_path / "phase_completion.csv"
    report = tmp_path / "phase_completion.md"

    validation = run(out_path=out, report_path=report)

    assert out.is_file()
    assert report.is_file()
    assert validation.rows == 35
    assert validation.phases == 7
    reread = validate_phase_completion_audit_csv(out)
    assert reread.rows == validation.rows


def test_readiness_parses_phase_completion_gate(tmp_path: Path):
    audit = tmp_path / "phase_completion.csv"
    with audit.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "phase",
                "task_id",
                "task",
                "status",
                "required_for_submission",
                "evidence",
                "reason",
                "next_action",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "phase": "P2-0",
                "task_id": "P2-0-1",
                "task": "plan",
                "status": STATUS_READY,
                "required_for_submission": "true",
                "evidence": "plan.md",
                "reason": "ready",
                "next_action": "archive",
            }
        )

    rows = build_audit(skip_franka_probe=True, phase_completion_audit_path=audit)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:phase_completion_evidence"].status == STATUS_READY
    assert "rows=1" in by_gate["gate:phase_completion_evidence"].evidence
