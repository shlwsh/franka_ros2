import csv
from pathlib import Path

from doctor.paper2.experiments.run_ontology_identifier_audit import (
    EVIDENCE_FIELDNAMES,
    run,
    validate_ontology_identifier_audit_csv,
)


def _write_evidence(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=EVIDENCE_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def _valid_rows() -> list[dict[str, str]]:
    entities = [
        "fever",
        "sore_throat",
        "cold_aversion",
        "mouth_bitter",
        "nausea",
        "fatigue",
        "red_tongue",
        "pale_tongue",
        "yellow_greasy_coating",
        "thin_white_coating",
    ]
    rows: list[dict[str, str]] = []
    for idx, entity in enumerate(entities, start=1):
        is_visual = "tongue" in entity or "coating" in entity
        rows.append(
            {
                "entity": entity,
                "category": "visual_finding" if is_visual else "symptom",
                "local_code": f"P2MAP{idx:03d}",
                "fhir_target": "Observation.component" if is_visual else "Observation.code",
                "icd_identifier": f"ICD11-TEST-{idx:03d}" if not is_visual else "",
                "snomed_identifier": f"SCTID-{100000 + idx}",
                "license_status": "licensed-approved",
                "approval_evidence_uri": "/secure/paper2/ontology/approval.md",
                "source_release": "test-release",
                "source_artifact_sha256": "b" * 64,
                "mapping_basis": "derived mapping report without restricted text",
                "restricted_text_in_repo": "false",
            }
        )
    return rows


def test_missing_ontology_identifier_evidence_writes_template_and_blocked_audit(tmp_path: Path):
    validation = run(
        evidence_path=tmp_path / "missing.csv",
        out_path=tmp_path / "ontology_audit.csv",
        report_path=tmp_path / "ontology_audit.md",
        template_path=tmp_path / "ontology_template.csv",
        write_template_file=True,
    )

    assert not validation.ready
    assert validation.required_entities == 10
    assert validation.blocked_rows == 1
    assert (tmp_path / "ontology_template.csv").is_file()


def test_valid_ontology_identifier_evidence_marks_audit_ready(tmp_path: Path):
    evidence = tmp_path / "licensed_ontology_identifiers.csv"
    _write_evidence(evidence, _valid_rows())
    out = tmp_path / "ontology_audit.csv"

    validation = run(
        evidence_path=evidence,
        out_path=out,
        report_path=tmp_path / "ontology_audit.md",
    )
    reread = validate_ontology_identifier_audit_csv(out)

    assert validation.ready
    assert reread.ready
    assert validation.ready_rows == 10
    assert validation.covered_entities == 10


def test_placeholder_ontology_identifier_evidence_is_blocked(tmp_path: Path):
    rows = _valid_rows()
    rows[0]["snomed_identifier"] = "SNOMED_PLACEHOLDER"
    rows[0]["source_artifact_sha256"] = "not-a-hash"
    evidence = tmp_path / "licensed_ontology_identifiers.csv"
    _write_evidence(evidence, rows)

    validation = run(
        evidence_path=evidence,
        out_path=tmp_path / "ontology_audit.csv",
        report_path=tmp_path / "ontology_audit.md",
    )

    assert not validation.ready
    assert validation.blocked_rows == 1
    assert "placeholder-like" in validation.reason
    assert "SHA-256" in validation.reason
