from pathlib import Path

from doctor.paper2.experiments.run_expert_review import cohen_kappa, run
from doctor.paper2.langgraph_router.run import main as run_main


def test_cohen_kappa_handles_identical_labels():
    assert cohen_kappa([True, False, True], [True, False, True]) == 1.0


def test_expert_review_protocol_outputs(tmp_path: Path):
    log_path = tmp_path / "paper2.jsonl"
    packet = tmp_path / "review_packet.csv"
    annotations = tmp_path / "synthetic_annotations.csv"
    results = tmp_path / "expert_review_agreement.csv"
    report = tmp_path / "expert_review_protocol_report.md"
    protocol = tmp_path / "PROTOCOL.md"

    import sys

    argv = sys.argv
    try:
        sys.argv = ["run", "--trials", "8", "--log", str(log_path), "--results-dir", str(tmp_path / "results")]
        run_main()
    finally:
        sys.argv = argv

    agreement_rows = run(
        log_path=log_path,
        packet_path=packet,
        annotations_path=annotations,
        results_path=results,
        report_path=report,
        protocol_path=protocol,
        max_items_per_baseline=4,
    )

    assert packet.is_file()
    assert annotations.is_file()
    assert results.is_file()
    assert report.is_file()
    assert protocol.is_file()
    assert len(agreement_rows) == 3
    assert "Synthetic protocol validation only" in report.read_text(encoding="utf-8")
