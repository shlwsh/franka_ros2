from pathlib import Path

from doctor.paper2.experiments.run_kg_propagation import propagation_score, run
from doctor.paper2.kg.export_edges import export_edges


def test_export_edges_writes_csv(tmp_path: Path):
    out = tmp_path / "kg_edges.csv"
    count = export_edges(out_path=out)
    assert count == 11
    text = out.read_text(encoding="utf-8")
    assert "source,target,relation,weight,signed_weight" in text
    assert "cold_aversion,yellow_greasy_coating,contradict" in text


def test_propagation_scores_support_above_contradiction():
    support = propagation_score(
        [{"name": "fever"}],
        [{"name": "red_tongue"}],
    )
    contradiction = propagation_score(
        [{"name": "cold_aversion"}],
        [{"name": "yellow_greasy_coating"}],
    )
    assert support > 0
    assert contradiction < 0


def test_kg_propagation_experiment_writes_outputs(tmp_path: Path):
    out = tmp_path / "kg_propagation.csv"
    report = tmp_path / "kg_propagation_report.md"
    metrics = run(8, out, report)
    assert out.is_file()
    assert report.is_file()
    assert metrics["recall"] >= 0.6
