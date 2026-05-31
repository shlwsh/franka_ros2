import csv
from pathlib import Path

from doctor.paper2.experiments.run_readiness_audit import (
    STATUS_BLOCKED,
    STATUS_READY,
    _real_annotation_ready,
    build_audit,
    run,
)


def test_default_audit_marks_submission_gates_blocked_when_external_evidence_missing():
    rows = build_audit(skip_franka_probe=True)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:entity_map_coverage"].status == STATUS_READY
    assert by_gate["gate:licensed_ontology_identifiers"].status == STATUS_BLOCKED
    assert by_gate["gate:external_fhir_validator_config"].status == STATUS_BLOCKED
    assert by_gate["gate:real_dataset_main_experiment"].status == STATUS_BLOCKED
    assert by_gate["gate:large_gnn_gat_experiment"].status == STATUS_BLOCKED
    assert by_gate["gate:real_expert_review"].status == STATUS_BLOCKED
    assert by_gate["gate:bilingual_paper_artifacts"].status == STATUS_READY


def test_real_annotation_ready_requires_two_non_synthetic_reviewers(tmp_path: Path):
    packet = tmp_path / "review_packet.csv"
    with packet.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["review_item_id", "case_id"])
        writer.writeheader()
        writer.writerow({"review_item_id": "case_001", "case_id": "case_001"})

    annotations = tmp_path / "real_annotations.csv"
    with annotations.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "reviewer_id",
                "review_item_id",
                "factually_supported",
                "needs_human_review",
                "fhir_acceptable",
                "overall_score",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "reviewer_id": "expert_a",
                "review_item_id": "case_001",
                "factually_supported": "true",
                "needs_human_review": "false",
                "fhir_acceptable": "true",
                "overall_score": "4",
            }
        )
        writer.writerow(
            {
                "reviewer_id": "expert_b",
                "review_item_id": "case_001",
                "factually_supported": "true",
                "needs_human_review": "false",
                "fhir_acceptable": "true",
                "overall_score": "4",
            }
        )

    ready, reason = _real_annotation_ready(annotations, packet_path=packet)
    assert ready
    assert "2 reviewers" in reason


def test_run_writes_csv_and_markdown_reports(tmp_path: Path):
    out = tmp_path / "readiness.csv"
    report = tmp_path / "readiness.md"

    rows = run(out_path=out, report_path=report, skip_franka_probe=True)

    assert rows
    assert out.is_file()
    assert report.is_file()
    text = report.read_text(encoding="utf-8")
    assert "submission-ready: no" in text
    assert "gate:real_dataset_main_experiment" in text
