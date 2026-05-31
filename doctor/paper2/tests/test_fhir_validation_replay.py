from pathlib import Path

from doctor.paper2.experiments.run_fhir_validation_replay import run


def test_fhir_validation_replay_writes_bundle_artifacts(tmp_path: Path):
    out = tmp_path / "fhir_validator_replay.csv"
    report = tmp_path / "fhir_validator_replay_report.md"
    bundle_dir = tmp_path / "bundles"

    rows = run(trials=8, out_path=out, report_path=report, bundle_dir=bundle_dir)

    assert out.is_file()
    assert report.is_file()
    assert len(rows) == 40
    assert any(not row["valid"] for row in rows)
    assert any(row["valid"] for row in rows)
    first_bundle = bundle_dir / "B0" / "b0_fhir_0000.json"
    assert first_bundle.is_file()
    assert "local-structural" in report.read_text(encoding="utf-8")


def test_fhir_validation_replay_can_generate_all_valid(tmp_path: Path):
    rows = run(
        trials=4,
        out_path=tmp_path / "fhir_validator_replay.csv",
        report_path=tmp_path / "fhir_validator_replay_report.md",
        bundle_dir=tmp_path / "bundles",
        include_invalid=False,
    )
    assert all(row["valid"] for row in rows)
