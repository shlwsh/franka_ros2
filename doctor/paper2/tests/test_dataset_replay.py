from pathlib import Path

from doctor.paper2.experiments.run_dataset_replay import run


def test_dataset_replay_writes_outputs(tmp_path: Path):
    out = tmp_path / "dataset_replay.csv"
    log = tmp_path / "dataset_replay.jsonl"
    report = tmp_path / "dataset_replay_report.md"
    results = tmp_path / "results"

    summary = run(
        trials=6,
        out_path=out,
        log_path=log,
        report_path=report,
        results_dir=results,
        dataset_id="sample_open_csv",
    )

    assert out.is_file()
    assert log.is_file()
    assert report.is_file()
    assert (results / "paper2_summary.csv").is_file()
    assert len(summary) == 5
    assert "sample_open_csv" in report.read_text(encoding="utf-8")
    assert sum(1 for _ in log.open(encoding="utf-8")) == 30
