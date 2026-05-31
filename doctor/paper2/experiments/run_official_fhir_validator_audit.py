"""Audit exported Paper II Bundles with an external FHIR validator.

This script does not download or vendor the official validator. It consumes the
Bundle JSON files produced by ``run_fhir_validation_replay.py`` and a validator
command supplied through ``PAPER2_FHIR_VALIDATOR_CMD`` or ``--validator-cmd``.
For submission-grade evidence, the command should point to the official HL7
validator jar and the jar path should be provided or inferable so its SHA-256 can
be recorded.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import shlex
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.tools.fhir_validator import validate_external, validate_local

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_BUNDLE_DIR = ROOT / "experiments" / "fhir_bundles"
DEFAULT_OUT = ROOT / "experiments" / "results" / "official_fhir_validator_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "official_fhir_validator_audit_report.md"
DEFAULT_TIMEOUT_S = 30.0
EXCERPT_LIMIT = 500

STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_BLOCKED = "blocked"

FIELDNAMES = [
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
]


@dataclass(frozen=True)
class OfficialFhirAuditValidation:
    ready: bool
    rows: int
    bundle_rows: int
    local_valid: int
    local_valid_external_passed: int
    unexpected_rejects: int
    artifact_hash_present: bool
    reason: str


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _safe_excerpt(value: str) -> str:
    compact = " ".join(str(value or "").split())
    return compact[:EXCERPT_LIMIT]


def _as_bool(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes"}


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in FIELDNAMES})


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _infer_artifact_path(command_template: str) -> Path | None:
    try:
        tokens = shlex.split(command_template.format(path="__bundle__.json"))
    except ValueError:
        return None
    for idx, token in enumerate(tokens):
        if token == "-jar" and idx + 1 < len(tokens):
            return Path(tokens[idx + 1])
        if token.endswith(".jar"):
            return Path(token)
    return None


def _artifact_metadata(
    *,
    command_template: str,
    validator_artifact: Path | None,
) -> tuple[str, str, str]:
    artifact = validator_artifact or _infer_artifact_path(command_template)
    if artifact is None:
        return "", "", "validator artifact path was not provided or inferable"
    if not artifact.is_file():
        return str(artifact), "", f"validator artifact not found: {artifact}"
    return _display_path(artifact), _sha256(artifact), "validator artifact hash recorded"


def _metadata_row(
    *,
    status: str,
    command_template: str,
    validator_artifact: str = "",
    validator_artifact_sha256: str = "",
    reason: str,
) -> dict[str, Any]:
    return {
        "record_type": "metadata",
        "status": status,
        "mode": "external" if command_template else "missing-config",
        "validator_command": command_template,
        "validator_artifact": validator_artifact,
        "validator_artifact_sha256": validator_artifact_sha256,
        "reason": reason,
    }


def _bundle_status(local_valid: bool, external_valid: bool) -> tuple[str, str]:
    if local_valid and external_valid:
        return STATUS_READY, "none"
    if local_valid and not external_valid:
        return STATUS_BLOCKED, "local_valid_external_invalid"
    if not local_valid and external_valid:
        return STATUS_PARTIAL, "local_invalid_external_valid"
    return STATUS_READY, "local_invalid_external_invalid"


def _bundle_row(
    *,
    bundle_path: Path,
    bundle_dir: Path,
    command_template: str,
    validator_artifact: str,
    validator_artifact_sha256: str,
    timeout_s: float,
) -> dict[str, Any]:
    try:
        bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    except Exception as exc:  # noqa: BLE001 - audit should capture malformed artifacts
        return {
            "record_type": "bundle",
            "status": STATUS_BLOCKED,
            "bundle_path": _display_path(bundle_path),
            "baseline": bundle_path.parent.name,
            "mode": "read-error",
            "mismatch_type": "unreadable_bundle",
            "external_error_count": 1,
            "validator_command": command_template,
            "validator_artifact": validator_artifact,
            "validator_artifact_sha256": validator_artifact_sha256,
            "reason": f"bundle JSON could not be read: {exc}",
        }

    local = validate_local(bundle)
    external = validate_external(bundle, command_template, timeout_s=timeout_s)
    status, mismatch_type = _bundle_status(local.valid, external.valid)
    try:
        baseline = bundle_path.relative_to(bundle_dir).parts[0]
    except ValueError:
        baseline = bundle_path.parent.name
    return {
        "record_type": "bundle",
        "status": status,
        "bundle_path": _display_path(bundle_path),
        "baseline": baseline,
        "local_valid": local.valid,
        "external_valid": external.valid,
        "mode": external.mode,
        "mismatch_type": mismatch_type,
        "local_error_count": len(local.errors),
        "external_error_count": len(external.errors),
        "local_errors": "; ".join(local.errors),
        "external_errors": "; ".join(external.errors),
        "validator_command": command_template,
        "validator_artifact": validator_artifact,
        "validator_artifact_sha256": validator_artifact_sha256,
        "stdout_excerpt": _safe_excerpt(external.stdout),
        "stderr_excerpt": _safe_excerpt(external.stderr),
        "reason": (
            "local-valid bundle passed external validator"
            if local.valid and external.valid
            else "local-valid bundle failed external validator"
            if local.valid
            else "local-negative diagnostic bundle"
        ),
    }


def validate_official_audit_csv(
    path: Path = DEFAULT_OUT,
    *,
    require_artifact_hash: bool = True,
) -> OfficialFhirAuditValidation:
    if not path.is_file():
        return OfficialFhirAuditValidation(
            False,
            0,
            0,
            0,
            0,
            0,
            False,
            f"official FHIR validator audit CSV not found: {path}",
        )
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            return OfficialFhirAuditValidation(
                False,
                0,
                0,
                0,
                0,
                0,
                False,
                f"missing column(s): {', '.join(sorted(missing))}",
            )
        rows = list(reader)

    metadata_rows = [row for row in rows if row.get("record_type") == "metadata"]
    bundle_rows = [row for row in rows if row.get("record_type") == "bundle"]
    artifact_hash_present = any(row.get("validator_artifact_sha256") for row in metadata_rows)
    if metadata_rows and any(row.get("status") == STATUS_BLOCKED for row in metadata_rows):
        return OfficialFhirAuditValidation(
            False,
            len(rows),
            len(bundle_rows),
            0,
            0,
            0,
            artifact_hash_present,
            "; ".join(row.get("reason", "") for row in metadata_rows if row.get("reason")),
        )
    if require_artifact_hash and not artifact_hash_present:
        return OfficialFhirAuditValidation(
            False,
            len(rows),
            len(bundle_rows),
            0,
            0,
            0,
            False,
            "validator artifact SHA-256 is missing",
        )
    if not bundle_rows:
        return OfficialFhirAuditValidation(
            False,
            len(rows),
            0,
            0,
            0,
            0,
            artifact_hash_present,
            "official FHIR validator audit has no bundle rows",
        )

    local_valid_rows = [row for row in bundle_rows if _as_bool(row.get("local_valid"))]
    local_valid_external_passed = sum(
        1 for row in local_valid_rows if _as_bool(row.get("external_valid"))
    )
    unexpected_rejects = len(local_valid_rows) - local_valid_external_passed
    if not local_valid_rows:
        return OfficialFhirAuditValidation(
            False,
            len(rows),
            len(bundle_rows),
            0,
            0,
            unexpected_rejects,
            artifact_hash_present,
            "no locally valid Bundle artifacts were audited",
        )
    if unexpected_rejects:
        return OfficialFhirAuditValidation(
            False,
            len(rows),
            len(bundle_rows),
            len(local_valid_rows),
            local_valid_external_passed,
            unexpected_rejects,
            artifact_hash_present,
            f"{unexpected_rejects} local-valid bundle(s) failed external validation",
        )
    return OfficialFhirAuditValidation(
        True,
        len(rows),
        len(bundle_rows),
        len(local_valid_rows),
        local_valid_external_passed,
        0,
        artifact_hash_present,
        "all locally valid exported Bundles passed the external validator",
    )


def _write_report(
    report_path: Path,
    rows: list[dict[str, Any]],
    validation: OfficialFhirAuditValidation,
) -> None:
    bundle_rows = [row for row in rows if row.get("record_type") == "bundle"]
    local_invalid_external_valid = sum(
        1
        for row in bundle_rows
        if not _as_bool(row.get("local_valid")) and _as_bool(row.get("external_valid"))
    )
    lines = [
        "# Official FHIR Validator Audit Report",
        "",
        "External validation audit over exported Paper II Bundle JSON artifacts.",
        "",
        f"- rows: {validation.rows}",
        f"- bundle rows: {validation.bundle_rows}",
        f"- local-valid bundles: {validation.local_valid}",
        f"- local-valid external passes: {validation.local_valid_external_passed}",
        f"- unexpected rejects: {validation.unexpected_rejects}",
        f"- local-negative external passes: {local_invalid_external_valid}",
        f"- artifact hash present: {'yes' if validation.artifact_hash_present else 'no'}",
        f"- ready: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Baseline | Bundles | Local Valid | External Pass | Unexpected Reject |",
        "|---|---:|---:|---:|---:|",
    ]
    baselines = sorted({row.get("baseline", "") for row in bundle_rows if row.get("baseline")})
    for baseline in baselines:
        subset = [row for row in bundle_rows if row.get("baseline") == baseline]
        local_valid = [row for row in subset if _as_bool(row.get("local_valid"))]
        external_pass = sum(1 for row in local_valid if _as_bool(row.get("external_valid")))
        lines.append(
            f"| {baseline} | {len(subset)} | {len(local_valid)} | "
            f"{external_pass} | {len(local_valid) - external_pass} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    bundle_dir: Path = DEFAULT_BUNDLE_DIR,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    command_template: str | None = None,
    validator_artifact: Path | None = None,
    timeout_s: float = DEFAULT_TIMEOUT_S,
    max_bundles: int | None = None,
    require_artifact_hash: bool = True,
) -> OfficialFhirAuditValidation:
    command_template = command_template or os.getenv("PAPER2_FHIR_VALIDATOR_CMD")
    validator_artifact = validator_artifact or (
        Path(os.environ["PAPER2_FHIR_VALIDATOR_ARTIFACT"])
        if os.getenv("PAPER2_FHIR_VALIDATOR_ARTIFACT")
        else None
    )
    rows: list[dict[str, Any]] = []
    if not command_template:
        rows.append(
            _metadata_row(
                status=STATUS_BLOCKED,
                command_template="",
                reason="PAPER2_FHIR_VALIDATOR_CMD or --validator-cmd is required",
            )
        )
        _write_csv(out_path, rows)
        validation = validate_official_audit_csv(out_path, require_artifact_hash=require_artifact_hash)
        _write_report(report_path, rows, validation)
        return validation

    artifact_path, artifact_sha256, artifact_reason = _artifact_metadata(
        command_template=command_template,
        validator_artifact=validator_artifact,
    )
    metadata_status = (
        STATUS_READY
        if artifact_sha256 or not require_artifact_hash
        else STATUS_BLOCKED
    )
    rows.append(
        _metadata_row(
            status=metadata_status,
            command_template=command_template,
            validator_artifact=artifact_path,
            validator_artifact_sha256=artifact_sha256,
            reason=artifact_reason,
        )
    )

    bundle_paths = sorted(bundle_dir.rglob("*.json")) if bundle_dir.is_dir() else []
    if max_bundles is not None and max_bundles > 0:
        bundle_paths = bundle_paths[:max_bundles]
    if not bundle_paths:
        rows.append(
            {
                "record_type": "bundle",
                "status": STATUS_BLOCKED,
                "mode": "missing-bundles",
                "validator_command": command_template,
                "validator_artifact": artifact_path,
                "validator_artifact_sha256": artifact_sha256,
                "reason": f"no Bundle JSON files found under {bundle_dir}",
            }
        )
    else:
        rows.extend(
            _bundle_row(
                bundle_path=bundle_path,
                bundle_dir=bundle_dir,
                command_template=command_template,
                validator_artifact=artifact_path,
                validator_artifact_sha256=artifact_sha256,
                timeout_s=timeout_s,
            )
            for bundle_path in bundle_paths
        )

    _write_csv(out_path, rows)
    validation = validate_official_audit_csv(out_path, require_artifact_hash=require_artifact_hash)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", type=Path, default=DEFAULT_BUNDLE_DIR)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--validator-cmd", default=None)
    parser.add_argument("--validator-artifact", type=Path, default=None)
    parser.add_argument("--timeout-s", type=float, default=DEFAULT_TIMEOUT_S)
    parser.add_argument("--max-bundles", type=int, default=None)
    parser.add_argument("--no-require-artifact-hash", action="store_true")
    args = parser.parse_args()

    validation = run(
        bundle_dir=args.bundle_dir,
        out_path=args.out,
        report_path=args.report,
        command_template=args.validator_cmd,
        validator_artifact=args.validator_artifact,
        timeout_s=args.timeout_s,
        max_bundles=args.max_bundles,
        require_artifact_hash=not args.no_require_artifact_hash,
    )
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
