import csv
from pathlib import Path

from doctor.paper2.experiments.run_readiness_audit import (
    STATUS_BLOCKED,
    STATUS_READY,
    _real_annotation_ready,
    build_audit,
    run,
)


def test_default_audit_marks_submission_gates_blocked_when_external_evidence_missing(tmp_path: Path):
    rows = build_audit(
        skip_franka_probe=True,
        bilingual_sync_audit_path=tmp_path / "missing_bilingual_sync.csv",
    )
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:entity_map_coverage"].status == STATUS_READY
    assert by_gate["gate:licensed_ontology_identifiers"].status == STATUS_BLOCKED
    assert by_gate["gate:external_fhir_validator_config"].status == STATUS_BLOCKED
    assert by_gate["gate:real_dataset_main_experiment"].status == STATUS_BLOCKED
    assert by_gate["gate:large_gnn_gat_experiment"].status == STATUS_BLOCKED
    assert by_gate["gate:real_expert_review"].status == STATUS_BLOCKED
    assert by_gate["gate:bilingual_paper_artifacts"].status == STATUS_READY
    assert by_gate["gate:bilingual_paper_sync"].status == STATUS_BLOCKED


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


def test_valid_franka_closed_loop_evidence_marks_robot_gate_ready(tmp_path: Path):
    closed_loop = tmp_path / "franka_closed_loop.csv"
    with closed_loop.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "trial_id",
                "base_url",
                "probe_status",
                "skill_name",
                "skill_success",
                "latency_ms",
                "joints_ok",
                "skills_ok",
                "error",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "trial_id": "franka_0000",
                "base_url": "http://fake/api/v1",
                "probe_status": "online",
                "skill_name": "go_to_tongue_pose",
                "skill_success": "True",
                "latency_ms": "15.0",
                "joints_ok": "True",
                "skills_ok": "True",
                "error": "",
            }
        )

    rows = build_audit(skip_franka_probe=True, franka_closed_loop_evidence=closed_loop)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:gazebo_fr3_closed_loop"].status == STATUS_READY
    assert "successes=1" in by_gate["gate:gazebo_fr3_closed_loop"].reason


def test_valid_official_fhir_audit_marks_replay_gate_ready(tmp_path: Path):
    official_audit = tmp_path / "official_fhir_validator_audit.csv"
    with official_audit.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_type",
                "status",
                "bundle_path",
                "baseline",
                "local_valid",
                "external_valid",
                "mode",
                "mismatch_type",
                "local_error_count",
                "external_error_count",
                "local_errors",
                "external_errors",
                "validator_command",
                "validator_artifact",
                "validator_artifact_sha256",
                "stdout_excerpt",
                "stderr_excerpt",
                "reason",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_type": "metadata",
                "status": "ready",
                "mode": "external",
                "validator_command": "java -jar validator_cli.jar {path}",
                "validator_artifact": "validator_cli.jar",
                "validator_artifact_sha256": "0" * 64,
                "reason": "validator artifact hash recorded",
            }
        )
        writer.writerow(
            {
                "record_type": "bundle",
                "status": "ready",
                "bundle_path": "bundle.json",
                "baseline": "B4",
                "local_valid": "True",
                "external_valid": "True",
                "mode": "external",
                "mismatch_type": "none",
                "local_error_count": "0",
                "external_error_count": "0",
                "validator_command": "java -jar validator_cli.jar {path}",
                "validator_artifact": "validator_cli.jar",
                "validator_artifact_sha256": "0" * 64,
                "reason": "local-valid bundle passed external validator",
            }
        )

    rows = build_audit(skip_franka_probe=True, official_fhir_audit_path=official_audit)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:official_fhir_replay"].status == STATUS_READY
    assert "bundle_rows=1" in by_gate["gate:official_fhir_replay"].evidence


def test_valid_large_gnn_audit_marks_gnn_gate_ready(tmp_path: Path):
    large_gnn_audit = tmp_path / "large_gnn_evidence_audit.csv"
    with large_gnn_audit.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_type",
                "status",
                "experiment_id",
                "graph_source",
                "model_family",
                "node_count",
                "edge_count",
                "primary_metric",
                "primary_metric_value",
                "baseline_metric_value",
                "seed_count",
                "evidence_uri",
                "artifact_sha256",
                "reason",
                "next_action",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_type": "evidence",
                "status": "ready",
                "experiment_id": "large_gnn_001",
                "graph_source": "licensed graph",
                "model_family": "GAT",
                "node_count": "5000",
                "edge_count": "15000",
                "primary_metric": "macro_f1",
                "primary_metric_value": "0.8123",
                "baseline_metric_value": "0.7012",
                "seed_count": "3",
                "evidence_uri": "/secure/run.md",
                "artifact_sha256": "a" * 64,
                "reason": "large licensed-ontology GNN/GAT evidence passed audit",
                "next_action": "archive this evidence with the manuscript",
            }
        )

    rows = build_audit(skip_franka_probe=True, large_gnn_audit_path=large_gnn_audit)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:large_gnn_gat_experiment"].status == STATUS_READY
    assert "ready_rows=1" in by_gate["gate:large_gnn_gat_experiment"].evidence


def test_valid_ontology_identifier_audit_marks_ontology_gate_ready(tmp_path: Path):
    ontology_audit = tmp_path / "ontology_identifier_audit.csv"
    with ontology_audit.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_type",
                "status",
                "entity",
                "category",
                "local_code",
                "fhir_target",
                "icd_identifier_present",
                "snomed_identifier_present",
                "license_status",
                "approval_evidence_uri",
                "source_release",
                "source_artifact_sha256",
                "reason",
                "next_action",
            ],
        )
        writer.writeheader()
        for idx, entity in enumerate(
            [
                "cold_aversion",
                "fatigue",
                "fever",
                "mouth_bitter",
                "nausea",
                "pale_tongue",
                "red_tongue",
                "sore_throat",
                "thin_white_coating",
                "yellow_greasy_coating",
            ],
            start=1,
        ):
            writer.writerow(
                {
                    "record_type": "evidence",
                    "status": "ready",
                    "entity": entity,
                    "category": "symptom",
                    "local_code": f"P2MAP{idx:03d}",
                    "fhir_target": "Observation.code",
                    "icd_identifier_present": "True",
                    "snomed_identifier_present": "True",
                    "license_status": "licensed-approved",
                    "approval_evidence_uri": "/secure/approval.md",
                    "source_release": "test-release",
                    "source_artifact_sha256": "b" * 64,
                    "reason": "licensed ontology identifier evidence passed audit",
                    "next_action": "archive this mapping evidence with the manuscript",
                }
            )

    rows = build_audit(skip_franka_probe=True, ontology_audit_path=ontology_audit)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:licensed_ontology_identifiers"].status == STATUS_READY
    assert "covered=10/10" in by_gate["gate:licensed_ontology_identifiers"].evidence
