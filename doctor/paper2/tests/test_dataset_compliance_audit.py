import csv
import json
from pathlib import Path

from doctor.paper2.experiments.run_dataset_compliance_audit import (
    STATUS_BLOCKED,
    STATUS_READY,
    audit_registry,
    phi_flags_for_cases,
    run,
)


def test_dataset_compliance_default_registry_keeps_real_placeholders_blocked():
    rows = audit_registry()
    by_dataset = {row.dataset_id: row for row in rows}

    assert by_dataset["sample_open_csv"].status == STATUS_READY
    assert by_dataset["synthetic_builtin"].status == STATUS_READY
    assert by_dataset["mimic_iv_note_placeholder"].status == STATUS_BLOCKED
    assert by_dataset["mimic_cxr_placeholder"].status == STATUS_BLOCKED


def test_dataset_compliance_detects_phi_like_patterns():
    flags = phi_flags_for_cases(
        [
            {
                "case_id": "case_phi",
                "symptom_text": "Patient email test@example.com and MRN: ABCD1234.",
                "expected_entities": ["fever"],
                "vision_tags": ["red_tongue"],
                "q_img": 0.8,
                "conflict_label": False,
            }
        ]
    )
    assert "case_phi:email" in flags
    assert "case_phi:mrn" in flags


def test_dataset_compliance_run_writes_report(tmp_path: Path):
    out = tmp_path / "dataset_compliance.csv"
    report = tmp_path / "dataset_compliance.md"

    summary = run(out_path=out, report_path=report)

    assert summary["datasets"] >= 4
    assert summary["required_ready"] == 0
    assert out.is_file()
    assert "submission-dataset-ready: no" in report.read_text(encoding="utf-8")


def test_dataset_compliance_accepts_open_non_synthetic_file(tmp_path: Path):
    dataset_path = tmp_path / "cases.jsonl"
    dataset_path.write_text(
        json.dumps(
            {
                "case_id": "realish_001",
                "symptom_text": "Patient reports fever with no identifying text.",
                "expected_entities": ["fever"],
                "vision_tags": ["red_tongue"],
                "q_img": 0.82,
                "conflict_label": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    registry = tmp_path / "registry.json"
    registry.write_text(
        json.dumps(
            {
                "datasets": [
                    {
                        "dataset_id": "open_realish",
                        "name": "Open derived evaluation rows",
                        "source_type": "jsonl",
                        "access_level": "open",
                        "license": "open derived no-PHI rows",
                        "path": str(dataset_path),
                    }
                ]
            }
        ),
        encoding="utf-8",
    )

    rows = audit_registry(registry)

    assert len(rows) == 1
    assert rows[0].required_for_submission
    assert rows[0].status == STATUS_READY
    assert rows[0].case_count == 1


def test_readiness_can_parse_compliance_ready_csv(tmp_path: Path):
    from doctor.paper2.experiments.run_readiness_audit import _dataset_compliance_ready

    path = tmp_path / "dataset_compliance.csv"
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "dataset_id",
                "required_for_submission",
                "status",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "dataset_id": "open_realish",
                "required_for_submission": "true",
                "status": "ready",
            }
        )

    ready, reason = _dataset_compliance_ready(path)
    assert ready
    assert "open_realish" in reason
