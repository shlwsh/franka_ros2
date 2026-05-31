from pathlib import Path

from doctor.paper2.experiments.run_graph_embedding import embedding_score, run


def test_embedding_support_scores_above_contradiction():
    support = embedding_score(
        [{"name": "fever"}],
        [{"name": "red_tongue"}],
    )
    contradiction = embedding_score(
        [{"name": "cold_aversion"}],
        [{"name": "yellow_greasy_coating"}],
    )
    assert support > contradiction


def test_graph_embedding_experiment_writes_outputs(tmp_path: Path):
    out = tmp_path / "graph_embedding.csv"
    report = tmp_path / "graph_embedding_report.md"
    metrics = run(8, out, report)
    assert out.is_file()
    assert report.is_file()
    assert metrics["recall"] >= 0.6
