import hashlib
import json
import sys
from pathlib import Path

from doctor.paper2.agents.emr_fhir_agent import build_fhir_bundle
from doctor.paper2.experiments.run_official_fhir_validator_audit import (
    run,
    validate_official_audit_csv,
)


def _write_fake_validator(path: Path, *, reject_observation: bool = False) -> None:
    path.write_text(
        "\n".join(
            [
                "import json",
                "import sys",
                "bundle = json.loads(open(sys.argv[1], encoding='utf-8').read())",
                "types = [entry.get('resource', {}).get('resourceType') for entry in bundle.get('entry', [])]",
                "if 'Observation' not in types:",
                "    print('1 error: missing Observation')",
                "    raise SystemExit(1)",
                "if " + repr(reject_observation) + ":",
                "    print('1 error: rejected by fake validator')",
                "    raise SystemExit(1)",
                "print('0 errors')",
            ]
        )
        + "\n",
        encoding="utf-8",
    )


def test_missing_command_writes_blocked_audit(tmp_path: Path):
    out = tmp_path / "official_audit.csv"
    report = tmp_path / "official_audit.md"

    validation = run(
        bundle_dir=tmp_path / "bundles",
        out_path=out,
        report_path=report,
        command_template=None,
    )

    assert not validation.ready
    assert out.is_file()
    assert report.is_file()
    assert "PAPER2_FHIR_VALIDATOR_CMD" in validation.reason


def test_external_audit_accepts_local_valid_bundle_with_artifact_hash(tmp_path: Path):
    bundle_dir = tmp_path / "bundles" / "B4"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "b4_fhir_0000.json").write_text(
        json.dumps(build_fhir_bundle({"case_id": "audit_case", "assessment": "Synthetic"})),
        encoding="utf-8",
    )
    validator = tmp_path / "fake_validator.py"
    _write_fake_validator(validator)

    out = tmp_path / "official_audit.csv"
    report = tmp_path / "official_audit.md"
    validation = run(
        bundle_dir=tmp_path / "bundles",
        out_path=out,
        report_path=report,
        command_template=f"{sys.executable} {validator} {{path}}",
        validator_artifact=validator,
    )

    assert validation.ready
    assert validation.bundle_rows == 1
    assert validation.local_valid == 1
    assert validation.artifact_hash_present
    assert hashlib.sha256(validator.read_bytes()).hexdigest() in out.read_text(encoding="utf-8")


def test_external_audit_blocks_unexpected_reject(tmp_path: Path):
    bundle_dir = tmp_path / "bundles" / "B4"
    bundle_dir.mkdir(parents=True)
    (bundle_dir / "b4_fhir_0000.json").write_text(
        json.dumps(build_fhir_bundle({"case_id": "audit_case", "assessment": "Synthetic"})),
        encoding="utf-8",
    )
    validator = tmp_path / "fake_validator.py"
    _write_fake_validator(validator, reject_observation=True)
    out = tmp_path / "official_audit.csv"

    validation = run(
        bundle_dir=tmp_path / "bundles",
        out_path=out,
        report_path=tmp_path / "official_audit.md",
        command_template=f"{sys.executable} {validator} {{path}}",
        validator_artifact=validator,
    )
    reread = validate_official_audit_csv(out)

    assert not validation.ready
    assert not reread.ready
    assert validation.unexpected_rejects == 1
    assert "failed external validation" in validation.reason
