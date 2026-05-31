"""Audit licensed ontology identifier evidence for Paper II.

The tracked ``kg/entity_map.csv`` intentionally contains only project-local
codes and placeholders. This audit validates a separate evidence file for future
licensed ICD/SNOMED/FHIR identifiers without committing restricted ontology
text into the repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.kg.entity_map_coverage import DEFAULT_KG, DEFAULT_MAP, coverage_rows

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_EVIDENCE = ROOT / "kg" / "licensed_ontology_identifiers.csv"
DEFAULT_TEMPLATE = ROOT / "kg" / "licensed_ontology_identifiers.template.csv"
DEFAULT_OUT = ROOT / "experiments" / "results" / "ontology_identifier_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "ontology_identifier_audit_report.md"

STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
PLACEHOLDER_RE = re.compile(r"placeholder|stub|todo|tbd|example", re.I)
LICENSE_RE = re.compile(r"licensed|approved|authorized|credentialed", re.I)
FHIR_TARGETS = {"Observation.code", "Observation.component"}

EVIDENCE_FIELDNAMES = [
    "entity",
    "category",
    "local_code",
    "fhir_target",
    "icd_identifier",
    "snomed_identifier",
    "license_status",
    "approval_evidence_uri",
    "source_release",
    "source_artifact_sha256",
    "mapping_basis",
    "restricted_text_in_repo",
]

AUDIT_FIELDNAMES = [
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
]


@dataclass(frozen=True)
class OntologyIdentifierAuditValidation:
    ready: bool
    rows: int
    ready_rows: int
    blocked_rows: int
    required_entities: int
    covered_entities: int
    reason: str


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _kg_entities(kg_path: Path = DEFAULT_KG, map_path: Path = DEFAULT_MAP) -> list[dict[str, Any]]:
    rows = coverage_rows(kg_path=kg_path, map_path=map_path)
    return [row for row in rows if row.get("category") != "extra_mapping"]


def write_template(
    *,
    template_path: Path = DEFAULT_TEMPLATE,
    kg_path: Path = DEFAULT_KG,
    map_path: Path = DEFAULT_MAP,
) -> None:
    rows: list[dict[str, Any]] = []
    for row in _kg_entities(kg_path=kg_path, map_path=map_path):
        rows.append(
            {
                "entity": row["entity"],
                "category": row["category"],
                "local_code": "",
                "fhir_target": row["fhir_target"],
                "icd_identifier": "",
                "snomed_identifier": "",
                "license_status": "licensed-approved",
                "approval_evidence_uri": "path or URI to approval evidence",
                "source_release": "ontology release/version",
                "source_artifact_sha256": "64 lowercase hex characters",
                "mapping_basis": "derived mapping script/report; no restricted text",
                "restricted_text_in_repo": "false",
            }
        )
    _write_csv(template_path, rows, EVIDENCE_FIELDNAMES)


def _validate_evidence_row(row: dict[str, Any], required_entities: set[str]) -> tuple[str, str]:
    issues: list[str] = []
    entity = str(row.get("entity", "")).strip()
    if not entity:
        issues.append("entity is empty")
    elif entity not in required_entities:
        issues.append(f"entity is not in KG: {entity}")

    local_code = str(row.get("local_code", "")).strip()
    if not local_code:
        issues.append("local_code is empty")
    if PLACEHOLDER_RE.search(local_code):
        issues.append("local_code is placeholder-like")

    fhir_target = str(row.get("fhir_target", "")).strip()
    if fhir_target not in FHIR_TARGETS:
        issues.append("fhir_target is not an allowed Paper II target")

    icd_identifier = str(row.get("icd_identifier", "")).strip()
    snomed_identifier = str(row.get("snomed_identifier", "")).strip()
    if not icd_identifier and not snomed_identifier:
        issues.append("both ICD and SNOMED identifiers are empty")
    if icd_identifier and PLACEHOLDER_RE.search(icd_identifier):
        issues.append("icd_identifier is placeholder-like")
    if snomed_identifier and PLACEHOLDER_RE.search(snomed_identifier):
        issues.append("snomed_identifier is placeholder-like")

    license_status = str(row.get("license_status", "")).strip()
    if not LICENSE_RE.search(license_status):
        issues.append("license_status does not show approval/licensing")
    if PLACEHOLDER_RE.search(license_status):
        issues.append("license_status is placeholder-like")

    if not str(row.get("approval_evidence_uri", "")).strip():
        issues.append("approval_evidence_uri is empty")
    if not str(row.get("source_release", "")).strip():
        issues.append("source_release is empty")
    if not SHA256_RE.match(str(row.get("source_artifact_sha256", "")).strip()):
        issues.append("source_artifact_sha256 is not a SHA-256 hex digest")
    if not str(row.get("mapping_basis", "")).strip():
        issues.append("mapping_basis is empty")
    if _as_bool(row.get("restricted_text_in_repo", "")):
        issues.append("restricted_text_in_repo is true")

    if issues:
        return STATUS_BLOCKED, "; ".join(issues)
    return STATUS_READY, "licensed ontology identifier evidence passed audit"


def _audit_rows_from_evidence(
    evidence_rows: list[dict[str, Any]],
    *,
    kg_path: Path,
    map_path: Path,
) -> list[dict[str, Any]]:
    required_entities = {str(row["entity"]) for row in _kg_entities(kg_path=kg_path, map_path=map_path)}
    seen: set[str] = set()
    rows: list[dict[str, Any]] = []
    for evidence in evidence_rows:
        status, reason = _validate_evidence_row(evidence, required_entities)
        entity = str(evidence.get("entity", "")).strip()
        if entity in seen:
            status = STATUS_BLOCKED
            reason = f"{reason}; duplicate entity row" if reason else "duplicate entity row"
        seen.add(entity)
        rows.append(
            {
                "record_type": "evidence",
                "status": status,
                "entity": entity,
                "category": evidence.get("category", ""),
                "local_code": evidence.get("local_code", ""),
                "fhir_target": evidence.get("fhir_target", ""),
                "icd_identifier_present": bool(str(evidence.get("icd_identifier", "")).strip()),
                "snomed_identifier_present": bool(str(evidence.get("snomed_identifier", "")).strip()),
                "license_status": evidence.get("license_status", ""),
                "approval_evidence_uri": evidence.get("approval_evidence_uri", ""),
                "source_release": evidence.get("source_release", ""),
                "source_artifact_sha256": evidence.get("source_artifact_sha256", ""),
                "reason": reason,
                "next_action": (
                    "archive this mapping evidence with the manuscript"
                    if status == STATUS_READY
                    else "replace placeholders with licensed identifiers and approval evidence"
                ),
            }
        )

    missing_entities = sorted(required_entities - seen)
    for entity in missing_entities:
        rows.append(
            {
                "record_type": "missing",
                "status": STATUS_BLOCKED,
                "entity": entity,
                "reason": "licensed identifier evidence is missing for this KG entity",
                "next_action": "add a licensed evidence row for this entity",
            }
        )
    return rows


def validate_ontology_identifier_audit_csv(
    path: Path = DEFAULT_OUT,
    *,
    kg_path: Path = DEFAULT_KG,
    map_path: Path = DEFAULT_MAP,
) -> OntologyIdentifierAuditValidation:
    required_entities = {str(row["entity"]) for row in _kg_entities(kg_path=kg_path, map_path=map_path)}
    if not path.is_file():
        return OntologyIdentifierAuditValidation(
            False,
            0,
            0,
            0,
            len(required_entities),
            0,
            f"ontology identifier audit CSV not found: {path}",
        )
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(AUDIT_FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            return OntologyIdentifierAuditValidation(
                False,
                0,
                0,
                0,
                len(required_entities),
                0,
                f"missing column(s): {', '.join(sorted(missing))}",
            )
        rows = list(reader)

    ready_rows = [row for row in rows if row.get("status") == STATUS_READY]
    blocked_rows = [row for row in rows if row.get("status") != STATUS_READY]
    covered_entities = {row.get("entity", "") for row in ready_rows}
    ready = bool(required_entities) and covered_entities == required_entities and not blocked_rows
    if ready:
        reason = f"{len(ready_rows)} licensed ontology identifier row(s) passed audit"
    else:
        reasons = [row.get("reason", "") for row in blocked_rows if row.get("reason")]
        reason = "; ".join(reasons[:5]) or "licensed ontology identifier evidence is incomplete"
    return OntologyIdentifierAuditValidation(
        ready,
        len(rows),
        len(ready_rows),
        len(blocked_rows),
        len(required_entities),
        len(covered_entities),
        reason,
    )


def _write_report(
    report_path: Path,
    rows: list[dict[str, Any]],
    validation: OntologyIdentifierAuditValidation,
) -> None:
    lines = [
        "# Ontology Identifier Audit Report",
        "",
        "Conservative audit for licensed ICD/SNOMED/FHIR identifier evidence.",
        "",
        f"- rows: {validation.rows}",
        f"- ready rows: {validation.ready_rows}",
        f"- blocked rows: {validation.blocked_rows}",
        f"- required entities: {validation.required_entities}",
        f"- covered entities: {validation.covered_entities}",
        f"- ready: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Entity | Status | ICD | SNOMED | License | Reason |",
        "|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('entity', '')} | {row.get('status', '')} | "
            f"{row.get('icd_identifier_present', '')} | "
            f"{row.get('snomed_identifier_present', '')} | "
            f"{row.get('license_status', '')} | {row.get('reason', '')} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    evidence_path: Path = DEFAULT_EVIDENCE,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    template_path: Path = DEFAULT_TEMPLATE,
    write_template_file: bool = False,
    kg_path: Path = DEFAULT_KG,
    map_path: Path = DEFAULT_MAP,
) -> OntologyIdentifierAuditValidation:
    if write_template_file:
        write_template(template_path=template_path, kg_path=kg_path, map_path=map_path)

    if not evidence_path.is_file():
        rows = [
            {
                "record_type": "metadata",
                "status": STATUS_BLOCKED,
                "reason": f"licensed ontology identifier CSV not found: {_display_path(evidence_path)}",
                "next_action": (
                    "obtain ontology approval, derive mappings outside the repo, and fill "
                    f"{_display_path(template_path)}"
                ),
            }
        ]
        _write_csv(out_path, rows, AUDIT_FIELDNAMES)
        validation = validate_ontology_identifier_audit_csv(out_path, kg_path=kg_path, map_path=map_path)
        _write_report(report_path, rows, validation)
        return validation

    with evidence_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(EVIDENCE_FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            rows = [
                {
                    "record_type": "metadata",
                    "status": STATUS_BLOCKED,
                    "reason": f"evidence CSV missing column(s): {', '.join(sorted(missing))}",
                    "next_action": "repair the licensed ontology identifier CSV schema",
                }
            ]
        else:
            rows = _audit_rows_from_evidence(list(reader), kg_path=kg_path, map_path=map_path)

    _write_csv(out_path, rows, AUDIT_FIELDNAMES)
    validation = validate_ontology_identifier_audit_csv(out_path, kg_path=kg_path, map_path=map_path)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--kg", type=Path, default=DEFAULT_KG)
    parser.add_argument("--map", type=Path, default=DEFAULT_MAP)
    args = parser.parse_args()

    validation = run(
        evidence_path=args.evidence,
        out_path=args.out,
        report_path=args.report,
        template_path=args.template,
        write_template_file=args.write_template,
        kg_path=args.kg,
        map_path=args.map,
    )
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
