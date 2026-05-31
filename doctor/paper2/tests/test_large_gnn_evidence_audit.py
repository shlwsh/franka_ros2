import csv
from pathlib import Path

from doctor.paper2.experiments.run_large_gnn_evidence_audit import (
    EVIDENCE_FIELDNAMES,
    run,
    validate_large_gnn_audit_csv,
)


def _write_evidence(path: Path, row: dict[str, str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EVIDENCE_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerow(row)


def _valid_row() -> dict[str, str]:
    return {
        "experiment_id": "large_gnn_001",
        "graph_source": "licensed ontology-derived graph",
        "license_status": "licensed-approved",
        "ontology_identifier_status": "licensed-non-placeholder",
        "node_count": "5000",
        "edge_count": "15000",
        "model_family": "GAT",
        "framework": "PyTorch Geometric",
        "train_size": "3000",
        "validation_size": "1000",
        "test_size": "1000",
        "primary_metric": "macro_f1",
        "primary_metric_value": "0.8123",
        "baseline_metric_value": "0.7012",
        "seed_count": "3",
        "evidence_uri": "/secure/paper2/large_gnn/run_001/report.md",
        "artifact_sha256": "a" * 64,
        "uses_synthetic_or_stub": "false",
        "notes": "derived no-PHI feature graph; no restricted ontology text in repo",
    }


def test_missing_large_gnn_evidence_writes_blocked_audit(tmp_path: Path):
    validation = run(
        evidence_path=tmp_path / "missing.csv",
        out_path=tmp_path / "large_gnn_audit.csv",
        report_path=tmp_path / "large_gnn_audit.md",
        template_path=tmp_path / "large_gnn_template.csv",
        write_template_file=True,
    )

    assert not validation.ready
    assert "not found" in validation.reason
    assert validation.blocked_rows == 1
    assert (tmp_path / "large_gnn_template.csv").is_file()


def test_valid_large_gnn_evidence_marks_audit_ready(tmp_path: Path):
    evidence = tmp_path / "large_gnn_evidence.csv"
    _write_evidence(evidence, _valid_row())
    out = tmp_path / "large_gnn_audit.csv"

    validation = run(
        evidence_path=evidence,
        out_path=out,
        report_path=tmp_path / "large_gnn_audit.md",
    )
    reread = validate_large_gnn_audit_csv(out)

    assert validation.ready
    assert reread.ready
    assert validation.ready_rows == 1
    assert validation.max_node_count == 5000


def test_stub_large_gnn_evidence_is_blocked(tmp_path: Path):
    row = _valid_row()
    row["graph_source"] = "kg_stub synthetic toy graph"
    row["node_count"] = "10"
    row["edge_count"] = "11"
    row["uses_synthetic_or_stub"] = "true"
    evidence = tmp_path / "large_gnn_evidence.csv"
    _write_evidence(evidence, row)

    validation = run(
        evidence_path=evidence,
        out_path=tmp_path / "large_gnn_audit.csv",
        report_path=tmp_path / "large_gnn_audit.md",
    )

    assert not validation.ready
    assert "synthetic/stub" in validation.reason
    assert "node_count" in validation.reason
