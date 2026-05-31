from pathlib import Path

from doctor.paper2.experiments.run_graph_attention import (
    build_training_rows,
    graph_attention_score,
    initialize_weights,
    run,
    train_attention,
)
from doctor.paper2.agents.kg_conflict_agent import load_kg


def test_train_attention_increases_conflict_separation():
    kg = load_kg()
    rows = build_training_rows(8, kg)
    weights = train_attention(rows, kg["entities"], epochs=80)
    conflict_scores = [
        graph_attention_score(row, weights) for row in rows if row["conflict_label"] == 1.0
    ]
    clear_scores = [
        graph_attention_score(row, weights) for row in rows if row["conflict_label"] == 0.0
    ]
    assert sum(conflict_scores) / len(conflict_scores) > sum(clear_scores) / len(clear_scores)


def test_initialize_weights_has_expected_attention_direction():
    weights = initialize_weights(["fever", "red_tongue"])
    assert weights["support_attention"] < 0
    assert weights["contradiction_attention"] > 0


def test_graph_attention_experiment_writes_outputs(tmp_path: Path):
    out = tmp_path / "graph_attention.csv"
    report = tmp_path / "graph_attention_report.md"
    result = run(16, out, report, epochs=80)
    assert out.is_file()
    assert report.is_file()
    assert result["metrics"]["recall"] >= 0.8
    assert "support_attention" in report.read_text(encoding="utf-8")
