"""Audit Paper II readiness gates for submission-grade evidence.

The audit is intentionally conservative. Synthetic fixtures can be marked ready
for software validation, but submission-critical gates stay blocked until the
corresponding external evidence exists in the workspace.
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import sys
from collections import Counter
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.agents.emr_fhir_agent import build_fhir_bundle
from doctor.paper2.experiments.run_dataset_compliance_audit import (
    DEFAULT_OUT as DEFAULT_DATASET_COMPLIANCE,
    STATUS_READY as DATASET_STATUS_READY,
)
from doctor.paper2.experiments.run_real_expert_review import load_and_validate_annotations
from doctor.paper2.kg.entity_map_coverage import coverage_rows, summarize
from doctor.paper2.tools.dataset_loader import (
    CONTROLLED_ACCESS_LEVELS,
    DEFAULT_REGISTRY_PATH,
    load_cases,
    load_dataset_registry,
)
from doctor.paper2.tools.fhir_validator import validate_external
from doctor.paper2.tools.franka_client import FrankaApiClient
from doctor.paper2.tools.franka_probe import probe

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "readiness_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "readiness_audit_report.md"
DEFAULT_FHIR_REPLAY = ROOT / "experiments" / "results" / "fhir_validator_replay.csv"
DEFAULT_DATASET_COMPLIANCE_AUDIT = DEFAULT_DATASET_COMPLIANCE
DEFAULT_GRAPH_ATTENTION = ROOT / "experiments" / "results" / "graph_attention.csv"
DEFAULT_LARGE_GNN_EVIDENCE = ROOT / "experiments" / "results" / "large_gnn_evidence.csv"
DEFAULT_FRANKA_EVIDENCE = ROOT / "experiments" / "results" / "franka_closed_loop.csv"
DEFAULT_PROTOCOL = ROOT / "experiments" / "expert_review" / "PROTOCOL.md"
DEFAULT_PACKET = ROOT / "experiments" / "expert_review" / "review_packet.csv"
DEFAULT_SYNTHETIC_ANNOTATIONS = ROOT / "experiments" / "expert_review" / "synthetic_annotations.csv"
DEFAULT_REAL_ANNOTATIONS = ROOT / "experiments" / "expert_review" / "real_annotations.csv"

STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_BLOCKED = "blocked"
VALID_STATUSES = {STATUS_READY, STATUS_PARTIAL, STATUS_BLOCKED}


@dataclass(frozen=True)
class AuditRow:
    gate: str
    status: str
    required_for_submission: bool
    evidence: str
    reason: str
    next_action: str

    def __post_init__(self) -> None:
        if self.status not in VALID_STATUSES:
            raise ValueError(f"invalid readiness status: {self.status}")

    def to_csv_row(self) -> dict[str, str]:
        row = asdict(self)
        row["required_for_submission"] = "true" if self.required_for_submission else "false"
        return {key: str(value) for key, value in row.items()}


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _row(
    gate: str,
    status: str,
    *,
    required: bool,
    evidence: str,
    reason: str,
    next_action: str,
) -> AuditRow:
    return AuditRow(
        gate=gate,
        status=status,
        required_for_submission=required,
        evidence=evidence,
        reason=reason,
        next_action=next_action,
    )


def _is_synthetic_record(record: dict[str, Any]) -> bool:
    joined = " ".join(
        str(record.get(field, "")).lower()
        for field in ("dataset_id", "name", "source_type", "license", "description")
    )
    return "synthetic" in joined or "fixture" in joined or "no-phi" in joined


def _resolve_registry_path(raw_path: str, registry_path: Path) -> Path:
    path = Path(raw_path)
    if not path.is_absolute():
        path = registry_path.parent / path
    return path


def _audit_one_dataset(
    dataset_id: str,
    record: dict[str, Any],
    *,
    registry_path: Path,
) -> tuple[AuditRow, bool]:
    access_level = str(record.get("access_level", "")).strip().lower()
    source_type = str(record.get("source_type", "")).strip().lower()
    required = not _is_synthetic_record(record)
    evidence = record.get("path") or record.get("local_path") or record.get("local_path_template") or ""

    if access_level in CONTROLLED_ACCESS_LEVELS:
        raw_local = record.get("path") or record.get("local_path")
        if raw_local:
            local_path = _resolve_registry_path(str(raw_local), registry_path)
            if local_path.is_file():
                return (
                    _row(
                        f"dataset:{dataset_id}",
                        STATUS_PARTIAL,
                        required=True,
                        evidence=_display_path(local_path),
                        reason=(
                            "controlled derived file exists, but credentialing and approval evidence "
                            "must be documented before main experiments"
                        ),
                        next_action="record IRB/data-use approval and run the registered replay",
                    ),
                    False,
                )
        return (
            _row(
                f"dataset:{dataset_id}",
                STATUS_BLOCKED,
                required=True,
                evidence=str(evidence or "registry placeholder"),
                reason="controlled-access dataset is only a placeholder or lacks a local derived file",
                next_action="complete credentialing, derive no-PHI rows outside the repo, and add a local_path",
            ),
            False,
        )

    try:
        cases = load_cases(dataset_id=dataset_id, registry_path=registry_path)
    except Exception as exc:  # noqa: BLE001 - audit should capture all loader failures
        return (
            _row(
                f"dataset:{dataset_id}",
                STATUS_BLOCKED,
                required=required,
                evidence=str(evidence or registry_path),
                reason=f"dataset failed to load: {exc}",
                next_action="fix the registry path or dataset schema",
            ),
            False,
        )

    real_ready = bool(cases) and required
    return (
        _row(
            f"dataset:{dataset_id}",
            STATUS_READY,
            required=required,
            evidence=f"{len(cases)} case(s) load from {evidence or source_type}",
            reason="registered dataset loads through the Paper II dataset bridge",
            next_action="use this dataset for replay or keep as software fixture",
        ),
        real_ready,
    )


def _dataset_compliance_ready(path: Path) -> tuple[bool, str]:
    if not path.is_file():
        return False, f"dataset compliance audit missing: {_display_path(path)}"
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    required_rows = [row for row in rows if str(row.get("required_for_submission", "")).lower() == "true"]
    ready_required = [row for row in required_rows if row.get("status") == DATASET_STATUS_READY]
    if ready_required:
        dataset_ids = ", ".join(row.get("dataset_id", "") for row in ready_required)
        return True, f"{len(ready_required)} required dataset(s) compliance-ready: {dataset_ids}"
    if not required_rows:
        return False, "no required real dataset entries are present in the compliance audit"
    blocked = [row.get("dataset_id", "") for row in required_rows if row.get("status") != DATASET_STATUS_READY]
    return False, f"no required dataset passed compliance audit; blocked/partial: {', '.join(blocked)}"


def audit_dataset_registry(
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    *,
    compliance_audit_path: Path = DEFAULT_DATASET_COMPLIANCE_AUDIT,
) -> list[AuditRow]:
    try:
        registry = load_dataset_registry(registry_path)
    except Exception as exc:  # noqa: BLE001
        return [
            _row(
                "gate:dataset_registry",
                STATUS_BLOCKED,
                required=True,
                evidence=_display_path(registry_path),
                reason=f"registry cannot be read: {exc}",
                next_action="repair the dataset registry JSON",
            )
        ]

    if not registry:
        return [
            _row(
                "gate:dataset_registry",
                STATUS_BLOCKED,
                required=True,
                evidence=_display_path(registry_path),
                reason="dataset registry is empty",
                next_action="register at least one software fixture and one real evaluation dataset",
            )
        ]

    rows: list[AuditRow] = []
    real_ready_count = 0
    for dataset_id, record in sorted(registry.items()):
        row, real_ready = _audit_one_dataset(dataset_id, record, registry_path=registry_path)
        rows.append(row)
        real_ready_count += int(real_ready)

    compliance_ready, compliance_reason = _dataset_compliance_ready(compliance_audit_path)
    rows.append(
        _row(
            "gate:real_dataset_main_experiment",
            STATUS_READY if real_ready_count and compliance_ready else STATUS_BLOCKED,
            required=True,
            evidence=(
                f"{real_ready_count} non-synthetic registered dataset(s) load; "
                f"compliance={_display_path(compliance_audit_path)}"
            ),
            reason=(
                compliance_reason
                if real_ready_count
                else "only synthetic fixtures or controlled placeholders are currently ready"
            ),
            next_action=(
                "run dataset replay on the compliance-ready dataset"
                if real_ready_count and compliance_ready
                else "connect a licensed public/controlled no-PHI dataset, run compliance audit, and rerun dataset replay"
            ),
        )
    )
    return rows


def audit_entity_map() -> list[AuditRow]:
    try:
        summary = summarize(coverage_rows())
    except Exception as exc:  # noqa: BLE001
        return [
            _row(
                "gate:licensed_ontology_identifiers",
                STATUS_BLOCKED,
                required=True,
                evidence="doctor/paper2/kg/entity_map.csv",
                reason=f"entity map coverage failed: {exc}",
                next_action="repair the entity map and rerun entity_map_coverage.py",
            )
        ]

    coverage = float(summary["coverage"])
    placeholder_only = int(summary["placeholder_only"])
    rows = [
        _row(
            "gate:entity_map_coverage",
            STATUS_READY if coverage == 1.0 else STATUS_PARTIAL,
            required=False,
            evidence=(
                f"coverage={coverage:.4f}, fhir_target_coverage="
                f"{float(summary['fhir_target_coverage']):.4f}"
            ),
            reason="project-local KG entities have auditable placeholder mappings",
            next_action="keep coverage at 1.0 while replacing placeholders with licensed identifiers",
        )
    ]
    rows.append(
        _row(
            "gate:licensed_ontology_identifiers",
            STATUS_READY if coverage == 1.0 and placeholder_only == 0 else STATUS_BLOCKED,
            required=True,
            evidence=f"placeholder_only={placeholder_only}",
            reason=(
                "all entity mappings use licensed non-placeholder identifiers"
                if placeholder_only == 0
                else "ICD/SNOMED fields are still placeholder-only"
            ),
            next_action="replace placeholders with license-approved ICD/SNOMED identifiers",
        )
    )
    return rows


def audit_fhir_validator(
    *,
    command_template: str | None = None,
    replay_path: Path = DEFAULT_FHIR_REPLAY,
    timeout_s: float = 5.0,
) -> list[AuditRow]:
    rows: list[AuditRow] = []
    command_template = command_template or os.getenv("PAPER2_FHIR_VALIDATOR_CMD")
    if not command_template:
        rows.append(
            _row(
                "gate:external_fhir_validator_config",
                STATUS_BLOCKED,
                required=True,
                evidence="PAPER2_FHIR_VALIDATOR_CMD is unset",
                reason="only local structural validation is configured",
                next_action="set PAPER2_FHIR_VALIDATOR_CMD to the official FHIR validator CLI template",
            )
        )
    else:
        bundle = build_fhir_bundle(
            {"case_id": "readiness_audit", "assessment": "Readiness audit bundle"}
        )
        result = validate_external(bundle, command_template, timeout_s=timeout_s)
        rows.append(
            _row(
                "gate:external_fhir_validator_config",
                STATUS_READY if result.valid else STATUS_BLOCKED,
                required=True,
                evidence=f"mode={result.mode}, errors={len(result.errors)}",
                reason=(
                    "external validator accepted the readiness bundle"
                    if result.valid
                    else "; ".join(result.errors)
                ),
                next_action="run run_fhir_validation_replay.py with the same command",
            )
        )

    if not replay_path.is_file():
        rows.append(
            _row(
                "gate:official_fhir_replay",
                STATUS_BLOCKED,
                required=True,
                evidence=_display_path(replay_path),
                reason="FHIR replay CSV is missing",
                next_action="run run_fhir_validation_replay.py after configuring the official validator",
            )
        )
        return rows

    with replay_path.open(encoding="utf-8", newline="") as f:
        replay_rows = list(csv.DictReader(f))
    modes = sorted({row.get("mode", "") for row in replay_rows})
    all_external_valid = bool(replay_rows) and all(
        row.get("mode") == "external" and str(row.get("valid", "")).lower() == "true"
        for row in replay_rows
    )
    rows.append(
        _row(
            "gate:official_fhir_replay",
            STATUS_READY if all_external_valid else STATUS_BLOCKED,
            required=True,
            evidence=f"{len(replay_rows)} replay row(s), modes={', '.join(modes) or 'none'}",
            reason=(
                "all exported bundles passed external validation"
                if all_external_valid
                else "current replay is not an all-valid external official validator run"
            ),
            next_action="rerun FHIR replay with the official validator and resolve all errors",
        )
    )
    return rows


def franka_probe_row(result: dict[str, Any]) -> AuditRow:
    status = str(result.get("status", "offline"))
    if status == "online":
        readiness = STATUS_READY
        reason = "joints and skills endpoints are reachable"
        next_action = "run closed-loop trials and archive latency/tool-call CSVs"
    elif status == "partial":
        readiness = STATUS_PARTIAL
        reason = "only part of the franka_api_server tool surface is reachable"
        next_action = "repair offline endpoints before claiming robot closed-loop evidence"
    else:
        readiness = STATUS_BLOCKED
        errors = result.get("errors") or []
        reason = "; ".join(str(error) for error in errors) or "franka_api_server is offline"
        next_action = "start fake hardware/Gazebo/API or connect FR3, then rerun this audit"
    return _row(
        "gate:franka_api_server_probe",
        readiness,
        required=True,
        evidence=str(result.get("base_url", "unknown")),
        reason=reason,
        next_action=next_action,
    )


def audit_franka(
    *,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_s: float = 0.5,
    closed_loop_evidence: Path = DEFAULT_FRANKA_EVIDENCE,
    skip_probe: bool = False,
) -> list[AuditRow]:
    if skip_probe:
        rows = [
            _row(
                "gate:franka_api_server_probe",
                STATUS_PARTIAL,
                required=True,
                evidence="probe skipped",
                reason="runtime probe was disabled for this audit run",
                next_action="rerun without --skip-franka-probe before claiming robot evidence",
            )
        ]
    else:
        default_client = FrankaApiClient()
        client = FrankaApiClient(
            base_url=base_url or default_client.base_url,
            api_key=api_key or default_client.api_key,
            timeout_s=timeout_s,
        )
        rows = [franka_probe_row(probe(client))]

    rows.append(
        _row(
            "gate:gazebo_fr3_closed_loop",
            STATUS_READY if closed_loop_evidence.is_file() else STATUS_BLOCKED,
            required=True,
            evidence=_display_path(closed_loop_evidence),
            reason=(
                "robot closed-loop evidence CSV exists"
                if closed_loop_evidence.is_file()
                else "no Gazebo/FR3 closed-loop evidence CSV exists"
            ),
            next_action="run fake hardware/Gazebo or FR3 closed-loop trials and export the CSV",
        )
    )
    return rows


def audit_graph_evidence(
    *,
    graph_attention_path: Path = DEFAULT_GRAPH_ATTENTION,
    large_gnn_evidence: Path = DEFAULT_LARGE_GNN_EVIDENCE,
) -> list[AuditRow]:
    rows = [
        _row(
            "gate:graph_attention_lite",
            STATUS_READY if graph_attention_path.is_file() else STATUS_BLOCKED,
            required=False,
            evidence=_display_path(graph_attention_path),
            reason=(
                "dependency-light graph-attention-lite result exists"
                if graph_attention_path.is_file()
                else "graph-attention-lite result is missing"
            ),
            next_action="keep as a software baseline, not a substitute for the large graph experiment",
        )
    ]
    rows.append(
        _row(
            "gate:large_gnn_gat_experiment",
            STATUS_READY if large_gnn_evidence.is_file() else STATUS_BLOCKED,
            required=True,
            evidence=_display_path(large_gnn_evidence),
            reason=(
                "large graph evidence file exists"
                if large_gnn_evidence.is_file()
                else "no large licensed-ontology GNN/GAT evidence file exists"
            ),
            next_action="train/evaluate GNN or GAT on the licensed graph and archive the evidence CSV",
        )
    )
    return rows


def _real_annotation_ready(
    path: Path,
    *,
    packet_path: Path = DEFAULT_PACKET,
) -> tuple[bool, str]:
    try:
        rows = load_and_validate_annotations(packet_path=packet_path, annotations_path=path)
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)
    reviewers = {str(row["reviewer_id"]) for row in rows}
    item_ids = {str(row["review_item_id"]) for row in rows}
    return True, f"{len(rows)} rows, {len(item_ids)} items, {len(reviewers)} reviewers"


def audit_expert_review(
    *,
    protocol_path: Path = DEFAULT_PROTOCOL,
    packet_path: Path = DEFAULT_PACKET,
    synthetic_annotations_path: Path = DEFAULT_SYNTHETIC_ANNOTATIONS,
    real_annotations_path: Path = DEFAULT_REAL_ANNOTATIONS,
) -> list[AuditRow]:
    protocol_ready = protocol_path.is_file() and packet_path.is_file()
    real_ready, real_reason = _real_annotation_ready(real_annotations_path, packet_path=packet_path)
    return [
        _row(
            "gate:expert_review_protocol",
            STATUS_READY if protocol_ready else STATUS_BLOCKED,
            required=False,
            evidence=f"{_display_path(protocol_path)}, {_display_path(packet_path)}",
            reason=(
                "review protocol and packet exist"
                if protocol_ready
                else "review protocol or packet is missing"
            ),
            next_action="use the packet structure for real blinded review",
        ),
        _row(
            "gate:real_expert_review",
            STATUS_READY if real_ready else STATUS_BLOCKED,
            required=True,
            evidence=(
                f"{_display_path(real_annotations_path)}; synthetic="
                f"{_display_path(synthetic_annotations_path)}"
            ),
            reason=real_reason,
            next_action="collect real blinded annotations and replace synthetic agreement evidence",
        ),
    ]


def audit_paper_artifacts() -> list[AuditRow]:
    required_paths = [
        REPO_ROOT / "docs-zh" / "paper2" / "论文II_中文稿_20260531.md",
        REPO_ROOT / "docs-zh" / "paper2" / "PaperII_English_Draft_20260531.md",
        ROOT / "latex" / "main-zh.pdf",
        ROOT / "latex" / "main.pdf",
    ]
    missing = [path for path in required_paths if not path.is_file()]
    return [
        _row(
            "gate:bilingual_paper_artifacts",
            STATUS_READY if not missing else STATUS_BLOCKED,
            required=True,
            evidence=", ".join(_display_path(path) for path in required_paths),
            reason=(
                "Chinese and English Markdown/PDF artifacts exist"
                if not missing
                else "missing artifact(s): " + ", ".join(_display_path(path) for path in missing)
            ),
            next_action="keep both language versions synchronized after each evidence update",
        )
    ]


def build_audit(
    *,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    dataset_compliance_audit_path: Path = DEFAULT_DATASET_COMPLIANCE_AUDIT,
    fhir_command_template: str | None = None,
    fhir_timeout_s: float = 5.0,
    franka_base_url: str | None = None,
    franka_api_key: str | None = None,
    franka_timeout_s: float = 0.5,
    skip_franka_probe: bool = False,
    large_gnn_evidence: Path = DEFAULT_LARGE_GNN_EVIDENCE,
    franka_closed_loop_evidence: Path = DEFAULT_FRANKA_EVIDENCE,
    real_annotations_path: Path = DEFAULT_REAL_ANNOTATIONS,
) -> list[AuditRow]:
    rows: list[AuditRow] = []
    rows.extend(audit_dataset_registry(registry_path, compliance_audit_path=dataset_compliance_audit_path))
    rows.extend(audit_entity_map())
    rows.extend(
        audit_fhir_validator(
            command_template=fhir_command_template,
            timeout_s=fhir_timeout_s,
        )
    )
    rows.extend(
        audit_franka(
            base_url=franka_base_url,
            api_key=franka_api_key,
            timeout_s=franka_timeout_s,
            closed_loop_evidence=franka_closed_loop_evidence,
            skip_probe=skip_franka_probe,
        )
    )
    rows.extend(audit_graph_evidence(large_gnn_evidence=large_gnn_evidence))
    rows.extend(audit_expert_review(real_annotations_path=real_annotations_path))
    rows.extend(audit_paper_artifacts())
    return rows


def write_csv_report(rows: list[AuditRow], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8", newline="") as f:
        fieldnames = [
            "gate",
            "status",
            "required_for_submission",
            "evidence",
            "reason",
            "next_action",
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(row.to_csv_row() for row in rows)


def write_markdown_report(rows: list[AuditRow], report_path: Path) -> None:
    counts = Counter(row.status for row in rows)
    required_rows = [row for row in rows if row.required_for_submission]
    required_ready = sum(1 for row in required_rows if row.status == STATUS_READY)
    submission_ready = required_ready == len(required_rows)
    lines = [
        "# Paper II Readiness Audit Report",
        "",
        "Conservative audit of evidence gates required for a submission-grade Paper II.",
        "",
        f"- total gates: {len(rows)}",
        f"- ready: {counts[STATUS_READY]}",
        f"- partial: {counts[STATUS_PARTIAL]}",
        f"- blocked: {counts[STATUS_BLOCKED]}",
        f"- required gates ready: {required_ready}/{len(required_rows)}",
        f"- submission-ready: {'yes' if submission_ready else 'no'}",
        "",
        "| Gate | Status | Required | Evidence | Reason | Next Action |",
        "|---|---|---:|---|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.gate} | {row.status} | "
            f"{'yes' if row.required_for_submission else 'no'} | "
            f"{row.evidence} | {row.reason} | {row.next_action} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    dataset_compliance_audit_path: Path = DEFAULT_DATASET_COMPLIANCE_AUDIT,
    fhir_command_template: str | None = None,
    fhir_timeout_s: float = 5.0,
    franka_base_url: str | None = None,
    franka_api_key: str | None = None,
    franka_timeout_s: float = 0.5,
    skip_franka_probe: bool = False,
    large_gnn_evidence: Path = DEFAULT_LARGE_GNN_EVIDENCE,
    franka_closed_loop_evidence: Path = DEFAULT_FRANKA_EVIDENCE,
    real_annotations_path: Path = DEFAULT_REAL_ANNOTATIONS,
) -> list[AuditRow]:
    rows = build_audit(
        registry_path=registry_path,
        dataset_compliance_audit_path=dataset_compliance_audit_path,
        fhir_command_template=fhir_command_template,
        fhir_timeout_s=fhir_timeout_s,
        franka_base_url=franka_base_url,
        franka_api_key=franka_api_key,
        franka_timeout_s=franka_timeout_s,
        skip_franka_probe=skip_franka_probe,
        large_gnn_evidence=large_gnn_evidence,
        franka_closed_loop_evidence=franka_closed_loop_evidence,
        real_annotations_path=real_annotations_path,
    )
    write_csv_report(rows, out_path)
    write_markdown_report(rows, report_path)
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--registry", type=Path, default=DEFAULT_REGISTRY_PATH)
    parser.add_argument("--dataset-compliance-audit", type=Path, default=DEFAULT_DATASET_COMPLIANCE_AUDIT)
    parser.add_argument("--fhir-validator-cmd", default=None)
    parser.add_argument("--fhir-timeout-s", type=float, default=5.0)
    parser.add_argument("--franka-base-url", default=None)
    parser.add_argument("--franka-api-key", default=None)
    parser.add_argument("--franka-timeout-s", type=float, default=0.5)
    parser.add_argument("--skip-franka-probe", action="store_true")
    parser.add_argument("--large-gnn-evidence", type=Path, default=DEFAULT_LARGE_GNN_EVIDENCE)
    parser.add_argument("--franka-closed-loop-evidence", type=Path, default=DEFAULT_FRANKA_EVIDENCE)
    parser.add_argument("--real-annotations", type=Path, default=DEFAULT_REAL_ANNOTATIONS)
    args = parser.parse_args()

    rows = run(
        out_path=args.out,
        report_path=args.report,
        registry_path=args.registry,
        dataset_compliance_audit_path=args.dataset_compliance_audit,
        fhir_command_template=args.fhir_validator_cmd,
        fhir_timeout_s=args.fhir_timeout_s,
        franka_base_url=args.franka_base_url,
        franka_api_key=args.franka_api_key,
        franka_timeout_s=args.franka_timeout_s,
        skip_franka_probe=args.skip_franka_probe,
        large_gnn_evidence=args.large_gnn_evidence,
        franka_closed_loop_evidence=args.franka_closed_loop_evidence,
        real_annotations_path=args.real_annotations,
    )
    print(f"wrote readiness audit CSV to {args.out}")
    print(f"wrote readiness audit report to {args.report}")
    print(json.dumps(Counter(row.status for row in rows), indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
