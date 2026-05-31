"""Audit evidence for the Paper II large-graph GNN/GAT stage.

The dependency-light graph-attention-lite experiment is useful software
evidence, but it is not the licensed large-ontology GNN/GAT experiment required
for a submission-grade paper. This audit validates an external evidence CSV for
that stage and writes a blocked report when the real evidence is missing.
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

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_EVIDENCE = ROOT / "experiments" / "results" / "large_gnn_evidence.csv"
DEFAULT_OUT = ROOT / "experiments" / "results" / "large_gnn_evidence_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "large_gnn_evidence_audit_report.md"
DEFAULT_TEMPLATE = ROOT / "experiments" / "configs" / "large_gnn_evidence.template.csv"
DEFAULT_MIN_NODES = 1000
DEFAULT_MIN_EDGES = 1000

STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"
SHA256_RE = re.compile(r"^[0-9a-fA-F]{64}$")
MODEL_MARKERS = ("gat", "gnn", "gcn", "graphsage", "graph attention")
FORBIDDEN_MARKERS = ("synthetic", "stub", "placeholder-only", "placeholder only", "toy", "fixture")
LICENSE_MARKERS = ("licensed", "approved", "authorized", "credentialed")

EVIDENCE_FIELDNAMES = [
    "experiment_id",
    "graph_source",
    "license_status",
    "ontology_identifier_status",
    "node_count",
    "edge_count",
    "model_family",
    "framework",
    "train_size",
    "validation_size",
    "test_size",
    "primary_metric",
    "primary_metric_value",
    "baseline_metric_value",
    "seed_count",
    "evidence_uri",
    "artifact_sha256",
    "uses_synthetic_or_stub",
    "notes",
]

AUDIT_FIELDNAMES = [
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
]


@dataclass(frozen=True)
class LargeGnnAuditValidation:
    ready: bool
    rows: int
    ready_rows: int
    blocked_rows: int
    max_node_count: int
    max_edge_count: int
    reason: str


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "y"}


def _int_field(row: dict[str, Any], field: str) -> tuple[int | None, str | None]:
    try:
        value = int(str(row.get(field, "")).strip())
    except ValueError:
        return None, f"{field} is not an integer"
    if value < 0:
        return None, f"{field} is negative"
    return value, None


def _float_field(row: dict[str, Any], field: str) -> tuple[float | None, str | None]:
    try:
        value = float(str(row.get(field, "")).strip())
    except ValueError:
        return None, f"{field} is not numeric"
    if not 0.0 <= value <= 1.0:
        return None, f"{field} must be in [0, 1]"
    return value, None


def _contains_any(value: str, markers: tuple[str, ...]) -> bool:
    lowered = value.lower()
    return any(marker in lowered for marker in markers)


def _write_csv(path: Path, rows: list[dict[str, Any]], fieldnames: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def write_template(path: Path = DEFAULT_TEMPLATE) -> None:
    row = {
        "experiment_id": "large_gnn_001",
        "graph_source": "licensed ontology-derived graph name",
        "license_status": "licensed-approved",
        "ontology_identifier_status": "licensed-non-placeholder",
        "node_count": "0",
        "edge_count": "0",
        "model_family": "GAT",
        "framework": "PyTorch Geometric or DGL",
        "train_size": "0",
        "validation_size": "0",
        "test_size": "0",
        "primary_metric": "macro_f1",
        "primary_metric_value": "0.0000",
        "baseline_metric_value": "0.0000",
        "seed_count": "1",
        "evidence_uri": "path or URI to run report",
        "artifact_sha256": "64 lowercase hex characters",
        "uses_synthetic_or_stub": "false",
        "notes": "do not include restricted ontology text or PHI",
    }
    _write_csv(path, [row], EVIDENCE_FIELDNAMES)


def _validate_evidence_row(
    row: dict[str, Any],
    *,
    min_nodes: int,
    min_edges: int,
) -> tuple[str, str]:
    issues: list[str] = []
    experiment_id = str(row.get("experiment_id", "")).strip()
    if not experiment_id:
        issues.append("experiment_id is empty")

    graph_source = str(row.get("graph_source", "")).strip()
    license_status = str(row.get("license_status", "")).strip()
    identifier_status = str(row.get("ontology_identifier_status", "")).strip()
    joined_governance = " ".join([graph_source, license_status, identifier_status])
    if not graph_source:
        issues.append("graph_source is empty")
    if _contains_any(joined_governance, FORBIDDEN_MARKERS):
        issues.append("graph evidence is synthetic/stub/placeholder-like")
    if not _contains_any(license_status, LICENSE_MARKERS):
        issues.append("license_status does not show approval or licensing")
    if not _contains_any(identifier_status, LICENSE_MARKERS):
        issues.append("ontology identifiers are not marked licensed/approved")

    node_count, issue = _int_field(row, "node_count")
    if issue:
        issues.append(issue)
    elif node_count is not None and node_count < min_nodes:
        issues.append(f"node_count {node_count} below required {min_nodes}")

    edge_count, issue = _int_field(row, "edge_count")
    if issue:
        issues.append(issue)
    elif edge_count is not None and edge_count < min_edges:
        issues.append(f"edge_count {edge_count} below required {min_edges}")

    if node_count is not None and edge_count is not None and edge_count < node_count:
        issues.append("edge_count is below node_count")

    model_family = str(row.get("model_family", "")).strip()
    if not _contains_any(model_family, MODEL_MARKERS):
        issues.append("model_family is not a recognized GNN/GAT family")

    for field in ("train_size", "validation_size", "test_size", "seed_count"):
        value, issue = _int_field(row, field)
        if issue:
            issues.append(issue)
        elif value is not None and value < 1:
            issues.append(f"{field} must be >= 1")

    _, issue = _float_field(row, "primary_metric_value")
    if issue:
        issues.append(issue)
    _, issue = _float_field(row, "baseline_metric_value")
    if issue:
        issues.append(issue)

    if not str(row.get("primary_metric", "")).strip():
        issues.append("primary_metric is empty")
    if not str(row.get("evidence_uri", "")).strip():
        issues.append("evidence_uri is empty")
    if not SHA256_RE.match(str(row.get("artifact_sha256", "")).strip()):
        issues.append("artifact_sha256 is not a SHA-256 hex digest")
    if _as_bool(row.get("uses_synthetic_or_stub", "")):
        issues.append("uses_synthetic_or_stub is true")

    if issues:
        return STATUS_BLOCKED, "; ".join(issues)
    return STATUS_READY, "large licensed-ontology GNN/GAT evidence passed audit"


def _audit_rows_from_evidence(
    evidence_rows: list[dict[str, Any]],
    *,
    min_nodes: int,
    min_edges: int,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for row in evidence_rows:
        status, reason = _validate_evidence_row(row, min_nodes=min_nodes, min_edges=min_edges)
        rows.append(
            {
                "record_type": "evidence",
                "status": status,
                "experiment_id": row.get("experiment_id", ""),
                "graph_source": row.get("graph_source", ""),
                "model_family": row.get("model_family", ""),
                "node_count": row.get("node_count", ""),
                "edge_count": row.get("edge_count", ""),
                "primary_metric": row.get("primary_metric", ""),
                "primary_metric_value": row.get("primary_metric_value", ""),
                "baseline_metric_value": row.get("baseline_metric_value", ""),
                "seed_count": row.get("seed_count", ""),
                "evidence_uri": row.get("evidence_uri", ""),
                "artifact_sha256": row.get("artifact_sha256", ""),
                "reason": reason,
                "next_action": (
                    "archive this evidence with the manuscript"
                    if status == STATUS_READY
                    else "replace placeholder/stub evidence with a licensed large-graph GNN/GAT run"
                ),
            }
        )
    return rows


def validate_large_gnn_audit_csv(path: Path = DEFAULT_OUT) -> LargeGnnAuditValidation:
    if not path.is_file():
        return LargeGnnAuditValidation(
            False,
            0,
            0,
            0,
            0,
            0,
            f"large GNN/GAT audit CSV not found: {path}",
        )
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(AUDIT_FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            return LargeGnnAuditValidation(
                False,
                0,
                0,
                0,
                0,
                0,
                f"missing column(s): {', '.join(sorted(missing))}",
            )
        rows = list(reader)

    blocked_total = sum(1 for row in rows if row.get("status") != STATUS_READY)
    evidence_rows = [row for row in rows if row.get("record_type") == "evidence"]
    ready_rows = [row for row in evidence_rows if row.get("status") == STATUS_READY]
    blocked_rows = [row for row in evidence_rows if row.get("status") != STATUS_READY]
    node_counts = [int(row.get("node_count") or 0) for row in evidence_rows if str(row.get("node_count", "")).isdigit()]
    edge_counts = [int(row.get("edge_count") or 0) for row in evidence_rows if str(row.get("edge_count", "")).isdigit()]

    if not evidence_rows:
        reasons = "; ".join(row.get("reason", "") for row in rows if row.get("reason"))
        return LargeGnnAuditValidation(
            False,
            len(rows),
            0,
            blocked_total,
            max(node_counts or [0]),
            max(edge_counts or [0]),
            reasons or "large GNN/GAT audit has no evidence rows",
        )
    if ready_rows and not blocked_rows:
        return LargeGnnAuditValidation(
            True,
            len(rows),
            len(ready_rows),
            0,
            max(node_counts or [0]),
            max(edge_counts or [0]),
            f"{len(ready_rows)} large GNN/GAT evidence row(s) passed audit",
        )
    reasons = "; ".join(row.get("reason", "") for row in blocked_rows if row.get("reason"))
    return LargeGnnAuditValidation(
        False,
        len(rows),
        len(ready_rows),
        blocked_total,
        max(node_counts or [0]),
        max(edge_counts or [0]),
        reasons or "no large GNN/GAT evidence row passed audit",
    )


def _write_report(
    report_path: Path,
    rows: list[dict[str, Any]],
    validation: LargeGnnAuditValidation,
) -> None:
    lines = [
        "# Large GNN/GAT Evidence Audit Report",
        "",
        "Conservative audit for the licensed large-ontology graph experiment.",
        "",
        f"- rows: {validation.rows}",
        f"- ready rows: {validation.ready_rows}",
        f"- blocked rows: {validation.blocked_rows}",
        f"- max node count: {validation.max_node_count}",
        f"- max edge count: {validation.max_edge_count}",
        f"- ready: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Experiment | Status | Model | Nodes | Edges | Metric | Reason |",
        "|---|---|---|---:|---:|---|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('experiment_id', '')} | {row.get('status', '')} | "
            f"{row.get('model_family', '')} | {row.get('node_count', '')} | "
            f"{row.get('edge_count', '')} | {row.get('primary_metric', '')}="
            f"{row.get('primary_metric_value', '')} | {row.get('reason', '')} |"
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
    min_nodes: int = DEFAULT_MIN_NODES,
    min_edges: int = DEFAULT_MIN_EDGES,
) -> LargeGnnAuditValidation:
    if write_template_file:
        write_template(template_path)

    if not evidence_path.is_file():
        rows = [
            {
                "record_type": "metadata",
                "status": STATUS_BLOCKED,
                "experiment_id": "",
                "reason": f"large GNN/GAT evidence CSV not found: {_display_path(evidence_path)}",
                "next_action": (
                    "run a licensed ontology GNN/GAT experiment and fill "
                    f"{_display_path(template_path)}"
                ),
            }
        ]
        _write_csv(out_path, rows, AUDIT_FIELDNAMES)
        validation = validate_large_gnn_audit_csv(out_path)
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
                    "experiment_id": "",
                    "reason": f"evidence CSV missing column(s): {', '.join(sorted(missing))}",
                    "next_action": "repair the large GNN evidence CSV schema",
                }
            ]
        else:
            evidence_rows = list(reader)
            rows = _audit_rows_from_evidence(
                evidence_rows,
                min_nodes=min_nodes,
                min_edges=min_edges,
            )
            if not rows:
                rows = [
                    {
                        "record_type": "metadata",
                        "status": STATUS_BLOCKED,
                        "experiment_id": "",
                        "reason": "large GNN/GAT evidence CSV has no rows",
                        "next_action": "fill one row per completed large graph experiment",
                    }
                ]

    _write_csv(out_path, rows, AUDIT_FIELDNAMES)
    validation = validate_large_gnn_audit_csv(out_path)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, default=DEFAULT_EVIDENCE)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--template", type=Path, default=DEFAULT_TEMPLATE)
    parser.add_argument("--write-template", action="store_true")
    parser.add_argument("--min-nodes", type=int, default=DEFAULT_MIN_NODES)
    parser.add_argument("--min-edges", type=int, default=DEFAULT_MIN_EDGES)
    args = parser.parse_args()

    validation = run(
        evidence_path=args.evidence,
        out_path=args.out,
        report_path=args.report,
        template_path=args.template,
        write_template_file=args.write_template,
        min_nodes=args.min_nodes,
        min_edges=args.min_edges,
    )
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
