"""Audit Paper II dataset registry and derived case files.

The audit is a preflight gate for future public or controlled datasets. It
checks registry metadata, derived case-file schema, path placement, lightweight
PHI patterns, and approval-evidence pointers without copying source clinical
records into the repository.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.tools.dataset_loader import (
    CONTROLLED_ACCESS_LEVELS,
    DEFAULT_REGISTRY_PATH,
    load_cases,
    load_dataset_registry,
)

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "dataset_compliance_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "dataset_compliance_audit_report.md"
STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_BLOCKED = "blocked"
APPROVAL_FIELDS = (
    "approval_evidence_path",
    "data_use_approval_path",
    "credentialing_evidence_path",
)
PHI_PATTERNS = {
    "email": re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"),
    "phone": re.compile(r"\b(?:\+?\d[\d .-]{7,}\d)\b"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "mrn": re.compile(r"\b(?:MRN|medical record number)\s*[:#]?\s*[A-Z0-9-]{4,}\b", re.I),
    "precise_date": re.compile(r"\b(?:19|20)\d{2}-\d{2}-\d{2}\b|\b\d{1,2}/\d{1,2}/(?:19|20)?\d{2}\b"),
}


@dataclass(frozen=True)
class DatasetAuditRow:
    dataset_id: str
    access_level: str
    source_type: str
    required_for_submission: bool
    status: str
    case_count: int
    phi_flags: int
    evidence: str
    reason: str
    next_action: str

    def to_csv_row(self) -> dict[str, str]:
        row = asdict(self)
        row["required_for_submission"] = "true" if self.required_for_submission else "false"
        return {key: str(value) for key, value in row.items()}


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _is_synthetic_record(record: dict[str, Any]) -> bool:
    joined = " ".join(
        str(record.get(field, "")).lower()
        for field in ("dataset_id", "name", "source_type", "license", "description")
    )
    return "synthetic" in joined or "fixture" in joined or "project-local" in joined


def _resolve_record_path(record: dict[str, Any], registry_path: Path) -> Path | None:
    raw_path = record.get("path") or record.get("local_path")
    if not raw_path:
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = registry_path.parent / path
    return path


def _resolve_optional_path(raw_path: Any, registry_path: Path) -> Path | None:
    if not str(raw_path or "").strip():
        return None
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = registry_path.parent / path
    return path


def _has_approval_evidence(record: dict[str, Any], registry_path: Path) -> bool:
    for field in APPROVAL_FIELDS:
        path = _resolve_optional_path(record.get(field), registry_path)
        if path and path.is_file():
            return True
    return False


def _is_inside_repo(path: Path) -> bool:
    try:
        path.resolve().relative_to(REPO_ROOT.resolve())
        return True
    except ValueError:
        return False


def _iter_strings(value: Any) -> list[str]:
    if isinstance(value, str):
        return [value]
    if isinstance(value, dict):
        strings: list[str] = []
        for item in value.values():
            strings.extend(_iter_strings(item))
        return strings
    if isinstance(value, (list, tuple, set)):
        strings = []
        for item in value:
            strings.extend(_iter_strings(item))
        return strings
    return []


def phi_flags_for_cases(cases: list[dict[str, Any]]) -> list[str]:
    flags: list[str] = []
    for case in cases:
        case_id = str(case.get("case_id", "<unknown>"))
        for text in _iter_strings(case):
            for name, pattern in PHI_PATTERNS.items():
                if pattern.search(text):
                    flags.append(f"{case_id}:{name}")
    return flags


def _blocked_row(
    dataset_id: str,
    record: dict[str, Any],
    *,
    required: bool,
    evidence: str,
    reason: str,
    next_action: str,
) -> DatasetAuditRow:
    return DatasetAuditRow(
        dataset_id=dataset_id,
        access_level=str(record.get("access_level", "")),
        source_type=str(record.get("source_type", "")),
        required_for_submission=required,
        status=STATUS_BLOCKED,
        case_count=0,
        phi_flags=0,
        evidence=evidence,
        reason=reason,
        next_action=next_action,
    )


def audit_dataset_record(
    dataset_id: str,
    record: dict[str, Any],
    *,
    registry_path: Path,
) -> DatasetAuditRow:
    required = not _is_synthetic_record(record)
    access_level = str(record.get("access_level", "")).strip().lower()
    source_type = str(record.get("source_type", "")).strip()
    missing = [
        field
        for field in ("dataset_id", "access_level", "license", "source_type")
        if not str(record.get(field, "")).strip()
    ]
    if missing:
        return _blocked_row(
            dataset_id,
            record,
            required=required,
            evidence=_display_path(registry_path),
            reason=f"registry metadata missing: {', '.join(missing)}",
            next_action="repair dataset registry metadata",
        )

    path = _resolve_record_path(record, registry_path)
    if access_level in CONTROLLED_ACCESS_LEVELS and path is None:
        return _blocked_row(
            dataset_id,
            record,
            required=True,
            evidence=str(record.get("local_path_template") or "registry placeholder"),
            reason="controlled dataset has no local derived file path",
            next_action="derive no-PHI cases outside the repo and add local_path after approval",
        )

    if path and access_level in CONTROLLED_ACCESS_LEVELS and _is_inside_repo(path):
        return _blocked_row(
            dataset_id,
            record,
            required=True,
            evidence=_display_path(path),
            reason="controlled derived data path is inside the repository",
            next_action="keep controlled derived data outside the repository",
        )

    try:
        cases = load_cases(dataset_id=dataset_id, registry_path=registry_path, allow_controlled=True)
    except Exception as exc:  # noqa: BLE001
        return _blocked_row(
            dataset_id,
            record,
            required=required,
            evidence=_display_path(path) if path else str(record.get("local_path_template") or source_type),
            reason=f"derived cases failed schema/load audit: {exc}",
            next_action="fix the derived case file or registry path",
        )

    flags = phi_flags_for_cases(cases)
    if flags:
        return DatasetAuditRow(
            dataset_id=dataset_id,
            access_level=access_level,
            source_type=source_type,
            required_for_submission=required,
            status=STATUS_BLOCKED,
            case_count=len(cases),
            phi_flags=len(flags),
            evidence="; ".join(flags[:10]),
            reason="possible PHI-like pattern(s) found in derived cases",
            next_action="remove or de-identify flagged fields before replay",
        )

    if access_level in CONTROLLED_ACCESS_LEVELS and not _has_approval_evidence(record, registry_path):
        return DatasetAuditRow(
            dataset_id=dataset_id,
            access_level=access_level,
            source_type=source_type,
            required_for_submission=True,
            status=STATUS_PARTIAL,
            case_count=len(cases),
            phi_flags=0,
            evidence=_display_path(path) if path else "controlled derived path",
            reason="derived cases load and no PHI pattern was detected, but approval evidence is missing",
            next_action="add approval_evidence_path or credentialing_evidence_path outside source data",
        )

    return DatasetAuditRow(
        dataset_id=dataset_id,
        access_level=access_level,
        source_type=source_type,
        required_for_submission=required,
        status=STATUS_READY,
        case_count=len(cases),
        phi_flags=0,
        evidence=_display_path(path) if path else source_type,
        reason="dataset metadata and derived cases passed the preflight audit",
        next_action="run dataset replay or keep as a software fixture",
    )


def audit_registry(registry_path: Path = DEFAULT_REGISTRY_PATH) -> list[DatasetAuditRow]:
    registry = load_dataset_registry(registry_path)
    if not registry:
        return [
            DatasetAuditRow(
                dataset_id="<registry>",
                access_level="",
                source_type="",
                required_for_submission=True,
                status=STATUS_BLOCKED,
                case_count=0,
                phi_flags=0,
                evidence=_display_path(registry_path),
                reason="dataset registry is empty or missing",
                next_action="create a dataset registry with fixture and real-data entries",
            )
        ]
    return [
        audit_dataset_record(dataset_id, record, registry_path=registry_path)
        for dataset_id, record in sorted(registry.items())
    ]


def summarize(rows: list[DatasetAuditRow]) -> dict[str, Any]:
    required = [row for row in rows if row.required_for_submission]
    ready_required = [row for row in required if row.status == STATUS_READY]
    return {
        "datasets": len(rows),
        "ready": sum(1 for row in rows if row.status == STATUS_READY),
        "partial": sum(1 for row in rows if row.status == STATUS_PARTIAL),
        "blocked": sum(1 for row in rows if row.status == STATUS_BLOCKED),
        "required": len(required),
        "required_ready": len(ready_required),
        "submission_dataset_ready": bool(ready_required),
        "phi_flags": sum(row.phi_flags for row in rows),
    }


def write_outputs(rows: list[DatasetAuditRow], out_path: Path, report_path: Path) -> dict[str, Any]:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "dataset_id",
            "access_level",
            "source_type",
            "required_for_submission",
            "status",
            "case_count",
            "phi_flags",
            "evidence",
            "reason",
            "next_action",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in rows)

    summary = summarize(rows)
    lines = [
        "# Dataset Compliance Audit Report",
        "",
        "Preflight audit for Paper II dataset registry and derived no-PHI case files.",
        "",
        f"- datasets: {summary['datasets']}",
        f"- ready: {summary['ready']}",
        f"- partial: {summary['partial']}",
        f"- blocked: {summary['blocked']}",
        f"- required datasets ready: {summary['required_ready']}/{summary['required']}",
        f"- submission-dataset-ready: {'yes' if summary['submission_dataset_ready'] else 'no'}",
        f"- phi flags: {summary['phi_flags']}",
        "",
        "| Dataset | Status | Required | Cases | PHI Flags | Reason | Next Action |",
        "|---|---|---:|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.dataset_id} | {row.status} | "
            f"{'yes' if row.required_for_submission else 'no'} | "
            f"{row.case_count} | {row.phi_flags} | {row.reason} | {row.next_action} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return summary


def run(
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> dict[str, Any]:
    rows = audit_registry(registry_path)
    return write_outputs(rows, out_path, report_path)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    summary = run(registry_path=args.registry, out_path=args.out, report_path=args.report)
    print(f"wrote dataset compliance audit CSV to {args.out}")
    print(f"wrote dataset compliance audit report to {args.report}")
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
