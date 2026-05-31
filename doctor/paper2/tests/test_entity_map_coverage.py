from pathlib import Path

import pytest

from doctor.paper2.kg.entity_map_coverage import coverage_rows, run, summarize


def test_entity_map_covers_all_kg_entities():
    rows = coverage_rows()
    summary = summarize(rows)
    assert summary["kg_entities"] == 10
    assert summary["mapped_entities"] == 10
    assert summary["coverage"] == 1.0
    assert summary["fhir_target_coverage"] == 1.0


def test_entity_map_coverage_writes_outputs(tmp_path: Path):
    out = tmp_path / "entity_map_coverage.csv"
    report = tmp_path / "entity_map_coverage_report.md"
    summary = run(out_path=out, report_path=report)
    assert out.is_file()
    assert report.is_file()
    assert summary["placeholder_only"] == 10
    assert "No restricted ICD/SNOMED/UMLS" in report.read_text(encoding="utf-8")


def test_entity_map_rejects_missing_required_fields(tmp_path: Path):
    bad_map = tmp_path / "bad_entity_map.csv"
    bad_map.write_text("entity,category\nfever,symptom\n", encoding="utf-8")
    with pytest.raises(ValueError, match="missing fields"):
        coverage_rows(map_path=bad_map)
