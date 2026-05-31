import csv
import os
from pathlib import Path

from doctor.paper2.experiments.run_bilingual_sync_audit import (
    REQUIRED_CONCEPTS,
    STATUS_BLOCKED,
    STATUS_READY,
    run,
    validate_bilingual_sync_audit_csv,
)
from doctor.paper2.experiments.run_readiness_audit import build_audit


def _write_pair(tmp_path: Path, *, drop_en: str | None = None) -> dict[str, Path]:
    paths = {
        "zh": tmp_path / "paper-zh.md",
        "en": tmp_path / "paper-en.md",
        "zh_tex": tmp_path / "main-zh.tex",
        "en_tex": tmp_path / "main.tex",
        "zh_pdf": tmp_path / "main-zh.pdf",
        "en_pdf": tmp_path / "main.pdf",
    }

    zh_lines = [concept.zh_example for concept in REQUIRED_CONCEPTS]
    en_lines = [
        concept.en_example
        for concept in REQUIRED_CONCEPTS
        if concept.concept_id != drop_en
    ]
    zh_tex_lines = [concept.zh_example for concept in REQUIRED_CONCEPTS if concept.required_in_latex]
    en_tex_lines = [
        concept.en_example
        for concept in REQUIRED_CONCEPTS
        if concept.required_in_latex and concept.concept_id != drop_en
    ]

    paths["zh"].write_text("\n".join(zh_lines), encoding="utf-8")
    paths["en"].write_text("\n".join(en_lines), encoding="utf-8")
    paths["zh_tex"].write_text("\n".join(zh_tex_lines), encoding="utf-8")
    paths["en_tex"].write_text("\n".join(en_tex_lines), encoding="utf-8")
    paths["zh_pdf"].write_bytes(b"%PDF-1.4 zh\n")
    paths["en_pdf"].write_bytes(b"%PDF-1.4 en\n")
    paths["zh_pdf"].touch()
    paths["en_pdf"].touch()
    return paths


def test_bilingual_sync_audit_accepts_matching_concepts(tmp_path: Path):
    paths = _write_pair(tmp_path)
    out = tmp_path / "bilingual_sync.csv"
    report = tmp_path / "bilingual_sync.md"

    validation = run(
        zh_md_path=paths["zh"],
        en_md_path=paths["en"],
        zh_tex_path=paths["zh_tex"],
        en_tex_path=paths["en_tex"],
        zh_pdf_path=paths["zh_pdf"],
        en_pdf_path=paths["en_pdf"],
        out_path=out,
        report_path=report,
    )

    assert validation.ready
    assert validation.blocked_rows == 0
    assert out.is_file()
    assert report.is_file()
    reread = validate_bilingual_sync_audit_csv(out)
    assert reread.ready


def test_bilingual_sync_audit_blocks_missing_english_concept(tmp_path: Path):
    paths = _write_pair(tmp_path, drop_en="official_fhir_validator_blocked")
    out = tmp_path / "bilingual_sync.csv"

    validation = run(
        zh_md_path=paths["zh"],
        en_md_path=paths["en"],
        zh_tex_path=paths["zh_tex"],
        en_tex_path=paths["en_tex"],
        zh_pdf_path=paths["zh_pdf"],
        en_pdf_path=paths["en_pdf"],
        out_path=out,
        report_path=tmp_path / "bilingual_sync.md",
    )

    assert not validation.ready
    with out.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    blocked = [row for row in rows if row["status"] == STATUS_BLOCKED]
    assert blocked
    assert any(row["concept_id"] == "official_fhir_validator_blocked" for row in blocked)


def test_readiness_marks_bilingual_sync_ready_from_audit_csv(tmp_path: Path):
    audit = tmp_path / "bilingual_sync.csv"
    with audit.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "record_type",
                "concept_id",
                "status",
                "zh_hit",
                "en_hit",
                "zh_artifact",
                "en_artifact",
                "evidence",
                "reason",
                "next_action",
            ],
        )
        writer.writeheader()
        writer.writerow(
            {
                "record_type": "markdown_concept",
                "concept_id": "synthetic_mvp_scope",
                "status": STATUS_READY,
                "zh_hit": "True",
                "en_hit": "True",
                "zh_artifact": "paper-zh.md",
                "en_artifact": "paper-en.md",
                "evidence": "24 trial parity",
                "reason": "concept appears in both language artifacts",
                "next_action": "keep synchronized",
            }
        )

    rows = build_audit(skip_franka_probe=True, bilingual_sync_audit_path=audit)
    by_gate = {row.gate: row for row in rows}

    assert by_gate["gate:bilingual_paper_sync"].status == STATUS_READY
    assert "concept_rows=1" in by_gate["gate:bilingual_paper_sync"].evidence


def test_bilingual_sync_audit_blocks_stale_pdf(tmp_path: Path):
    paths = _write_pair(tmp_path)
    old_time = 1_700_000_000
    newer_time = old_time + 10

    os.utime(paths["zh_pdf"], (old_time, old_time))
    os.utime(paths["en_pdf"], (old_time, old_time))
    os.utime(paths["zh_tex"], (newer_time, newer_time))
    os.utime(paths["en_tex"], (newer_time, newer_time))

    validation = run(
        zh_md_path=paths["zh"],
        en_md_path=paths["en"],
        zh_tex_path=paths["zh_tex"],
        en_tex_path=paths["en_tex"],
        zh_pdf_path=paths["zh_pdf"],
        en_pdf_path=paths["en_pdf"],
        out_path=tmp_path / "bilingual_sync.csv",
        report_path=tmp_path / "bilingual_sync.md",
    )

    assert not validation.ready
    assert "stale artifact" in validation.reason
