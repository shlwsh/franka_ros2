import csv
from pathlib import Path

import pytest

from doctor.paper2.experiments.run_real_expert_review import (
    load_and_validate_annotations,
    run,
    write_annotation_template,
)


def _write_packet(path: Path, item_ids: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["review_item_id", "case_id"])
        writer.writeheader()
        for item_id in item_ids:
            writer.writerow({"review_item_id": item_id, "case_id": item_id})


def _write_annotations(path: Path, item_ids: list[str], reviewers: list[str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "reviewer_id",
                "review_item_id",
                "factually_supported",
                "needs_human_review",
                "fhir_acceptable",
                "overall_score",
            ],
        )
        writer.writeheader()
        for reviewer in reviewers:
            for item_id in item_ids:
                writer.writerow(
                    {
                        "reviewer_id": reviewer,
                        "review_item_id": item_id,
                        "factually_supported": "true",
                        "needs_human_review": "false",
                        "fhir_acceptable": "true",
                        "overall_score": "4",
                    }
                )


def test_real_expert_review_validates_and_writes_outputs(tmp_path: Path):
    packet = tmp_path / "review_packet.csv"
    annotations = tmp_path / "real_annotations.csv"
    results = tmp_path / "real_expert_review_agreement.csv"
    report = tmp_path / "real_expert_review_report.md"
    _write_packet(packet, ["review_001", "review_002"])
    _write_annotations(annotations, ["review_001", "review_002"], ["expert_a", "expert_b"])

    rows = run(
        packet_path=packet,
        annotations_path=annotations,
        results_path=results,
        report_path=report,
    )

    assert len(rows) == 3
    assert results.is_file()
    assert report.is_file()
    assert "Real Expert Review Report" in report.read_text(encoding="utf-8")


def test_real_expert_review_rejects_synthetic_reviewer(tmp_path: Path):
    packet = tmp_path / "review_packet.csv"
    annotations = tmp_path / "real_annotations.csv"
    _write_packet(packet, ["review_001"])
    _write_annotations(annotations, ["review_001"], ["R1_synthetic", "expert_b"])

    with pytest.raises(ValueError, match="synthetic"):
        load_and_validate_annotations(packet_path=packet, annotations_path=annotations)


def test_write_real_annotation_template(tmp_path: Path):
    packet = tmp_path / "review_packet.csv"
    template = tmp_path / "real_annotations.template.csv"
    _write_packet(packet, ["review_001", "review_002"])

    write_annotation_template(packet, template)

    text = template.read_text(encoding="utf-8")
    assert "reviewer_id,review_item_id" in text
    assert "review_001" in text
