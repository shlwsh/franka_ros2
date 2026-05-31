"""Generate Paper II MVP result figures from CSV outputs."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

try:
    import matplotlib.pyplot as plt
except ImportError as exc:  # pragma: no cover - exercised only in missing envs
    raise SystemExit("matplotlib is required to generate figures") from exc

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_RESULTS = ROOT / "experiments" / "results" / "paper2_summary.csv"
DEFAULT_KG_PROP = ROOT / "experiments" / "results" / "kg_propagation.csv"
DEFAULT_GRAPH_EMBED = ROOT / "experiments" / "results" / "graph_embedding.csv"
DEFAULT_GRAPH_ATTENTION = ROOT / "experiments" / "results" / "graph_attention.csv"
DEFAULT_DATASET_REPLAY = ROOT / "experiments" / "results" / "dataset_replay.csv"
DEFAULT_FHIR_REPLAY = ROOT / "experiments" / "results" / "fhir_validator_replay.csv"
DEFAULT_EXPERT_REVIEW = ROOT / "experiments" / "results" / "expert_review_agreement.csv"
DEFAULT_ENTITY_MAP = ROOT / "experiments" / "results" / "entity_map_coverage.csv"
DEFAULT_DATASET_COMPLIANCE = ROOT / "experiments" / "results" / "dataset_compliance_audit.csv"
DEFAULT_READINESS = ROOT / "experiments" / "results" / "readiness_audit.csv"
DEFAULT_OUT = ROOT / "figures"


def _load_numeric_rows(path: Path, label_keys: set[str]) -> list[dict[str, float | str | bool]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        rows: list[dict[str, float | str | bool]] = []
        for row in reader:
            parsed: dict[str, float | str | bool] = {}
            for key, value in row.items():
                if key in label_keys:
                    parsed[key] = value
                elif value in ("True", "False"):
                    parsed[key] = value == "True"
                else:
                    parsed[key] = float(value)
            rows.append(parsed)
    return rows


def _load_summary_rows(path: Path) -> list[dict[str, float | str]]:
    rows = _load_numeric_rows(path, {"baseline"})
    return [dict(row) for row in rows]  # type: ignore[list-item]


def _save(fig, out_dir: Path, stem: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.tight_layout()
    fig.savefig(out_dir / f"{stem}.svg")
    fig.savefig(out_dir / f"{stem}.pdf")
    plt.close(fig)


def plot_summary(rows: list[dict[str, float | str]], out_dir: Path) -> None:
    baselines = [str(row["baseline"]) for row in rows]
    metrics = [
        ("f1", "Conflict F1"),
        ("hallucination_rate", "Hallucination rate"),
        ("fhir_valid_rate", "FHIR valid rate"),
        ("tool_call_rate", "Tool call rate"),
    ]

    fig, axes = plt.subplots(2, 2, figsize=(9, 6))
    for ax, (key, title) in zip(axes.flatten(), metrics):
        values = [float(row[key]) for row in rows]
        ax.bar(baselines, values, color="#2f6f8f")
        ax.set_ylim(0, 1.05)
        ax.set_title(title)
        ax.set_xlabel("Baseline")
        ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_summary_metrics")


def plot_tradeoff(rows: list[dict[str, float | str]], out_dir: Path) -> None:
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    for row in rows:
        ax.scatter(
            float(row["hallucination_rate"]),
            float(row["fhir_valid_rate"]),
            s=80,
            color="#2f6f8f",
        )
        ax.annotate(str(row["baseline"]), (float(row["hallucination_rate"]), float(row["fhir_valid_rate"])))
    ax.set_xlabel("Hallucination rate")
    ax.set_ylabel("FHIR valid rate")
    ax.set_xlim(-0.03, 0.7)
    ax.set_ylim(-0.03, 0.85)
    ax.grid(alpha=0.25)
    _save(fig, out_dir, "paper2_hallucination_fhir_tradeoff")


def plot_kg_propagation(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(path, {"trial_id", "case_id", "conflict_type"})
    labels = [str(row["case_id"]) for row in rows]
    scores = [float(row["propagation_score"]) for row in rows]
    colors = ["#b84a4a" if bool(row["conflict_label"]) else "#2f6f8f" for row in rows]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(range(len(rows)), scores, color=colors)
    ax.axhline(0.0, color="#222222", linewidth=1.0)
    ax.set_ylabel("Signed propagation score")
    ax.set_xlabel("Synthetic case replay")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_kg_propagation_scores")


def plot_graph_embedding(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(path, {"trial_id", "case_id", "conflict_type"})
    labels = [str(row["case_id"]) for row in rows]
    scores = [float(row["embedding_score"]) for row in rows]
    colors = ["#b84a4a" if bool(row["conflict_label"]) else "#2f6f8f" for row in rows]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(range(len(rows)), scores, color=colors)
    ax.axhline(0.18, color="#222222", linewidth=1.0, linestyle="--")
    ax.set_ylabel("Embedding compatibility")
    ax.set_xlabel("Synthetic case replay")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_graph_embedding_scores")


def plot_graph_attention(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(path, {"trial_id", "case_id", "conflict_type"})
    labels = [str(row["case_id"]) for row in rows]
    scores = [float(row["attention_score"]) for row in rows]
    colors = ["#b84a4a" if bool(row["conflict_label"]) else "#2f6f8f" for row in rows]

    fig, ax = plt.subplots(figsize=(10, 4.5))
    ax.bar(range(len(rows)), scores, color=colors)
    ax.axhline(0.48, color="#222222", linewidth=1.0, linestyle="--")
    ax.set_ylabel("Trainable attention conflict score")
    ax.set_xlabel("Synthetic case replay")
    ax.set_xticks(range(len(rows)))
    ax.set_xticklabels(labels, rotation=60, ha="right", fontsize=7)
    ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_graph_attention_scores")


def plot_dataset_replay(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(
        path,
        {
            "dataset_id",
            "baseline",
            "trial_id",
            "case_id",
            "initial_route_decision",
            "final_route_decision",
            "fhir_validation_mode",
        },
    )
    by_baseline: dict[str, dict[str, float]] = {}
    for row in rows:
        baseline = str(row["baseline"])
        bucket = by_baseline.setdefault(
            baseline,
            {"rows": 0.0, "hallucination": 0.0, "fhir_valid": 0.0, "tool_calls": 0.0},
        )
        bucket["rows"] += 1.0
        bucket["hallucination"] += 1.0 if bool(row["hallucination_flag"]) else 0.0
        bucket["fhir_valid"] += 1.0 if bool(row["fhir_valid"]) else 0.0
        bucket["tool_calls"] += 1.0 if float(row["tool_calls"]) > 0 else 0.0

    baselines = sorted(by_baseline)
    hallucination = [
        by_baseline[item]["hallucination"] / by_baseline[item]["rows"] for item in baselines
    ]
    fhir_valid = [by_baseline[item]["fhir_valid"] / by_baseline[item]["rows"] for item in baselines]
    tool_calls = [by_baseline[item]["tool_calls"] / by_baseline[item]["rows"] for item in baselines]

    fig, ax = plt.subplots(figsize=(8, 4.8))
    x_positions = list(range(len(baselines)))
    width = 0.25
    ax.bar([x - width for x in x_positions], hallucination, width=width, label="Hallucination")
    ax.bar(x_positions, fhir_valid, width=width, label="FHIR valid")
    ax.bar([x + width for x in x_positions], tool_calls, width=width, label="Tool call")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(baselines)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Rate")
    ax.set_xlabel("Baseline")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, out_dir, "paper2_dataset_replay_rates")


def plot_fhir_validator_replay(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(
        path,
        {"baseline", "trial_id", "case_id", "bundle_path", "mode", "errors"},
    )
    by_baseline: dict[str, dict[str, float]] = {}
    for row in rows:
        bucket = by_baseline.setdefault(str(row["baseline"]), {"rows": 0.0, "valid": 0.0})
        bucket["rows"] += 1.0
        bucket["valid"] += 1.0 if bool(row["valid"]) else 0.0

    baselines = sorted(by_baseline)
    valid_rates = [by_baseline[item]["valid"] / by_baseline[item]["rows"] for item in baselines]

    fig, ax = plt.subplots(figsize=(7.5, 4.3))
    ax.bar(baselines, valid_rates, color="#2f6f8f")
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Bundle valid rate")
    ax.set_xlabel("Baseline")
    ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_fhir_validator_replay")


def plot_expert_review(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(path, {"metric"})
    labels = [str(row["metric"]).replace("_", "\n") for row in rows]
    kappas = [float(row["cohen_kappa"]) for row in rows]
    agreements = [float(row["agreement_rate"]) for row in rows]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    x_positions = list(range(len(labels)))
    width = 0.32
    ax.bar([x - width / 2 for x in x_positions], agreements, width=width, label="Agreement")
    ax.bar([x + width / 2 for x in x_positions], kappas, width=width, label="Cohen kappa")
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_xlabel("Synthetic review field")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, out_dir, "paper2_expert_review_agreement")


def plot_entity_map_coverage(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    rows = _load_numeric_rows(path, {"entity", "category", "fhir_target", "license_status"})
    total = len(rows)
    mapped = sum(1 for row in rows if bool(row["mapped"]))
    fhir_mapped = sum(1 for row in rows if str(row["fhir_target"]))
    placeholder = sum(1 for row in rows if str(row["license_status"]) == "placeholder-only")

    fig, ax = plt.subplots(figsize=(6.8, 4.2))
    labels = ["Entity map", "FHIR target", "Placeholder"]
    values = [mapped / total, fhir_mapped / total, placeholder / total]
    ax.bar(labels, values, color=["#2f6f8f", "#2f6f8f", "#b8a04a"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Coverage")
    ax.grid(axis="y", alpha=0.25)
    _save(fig, out_dir, "paper2_entity_map_coverage")


def plot_readiness_audit(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    statuses = ["ready", "partial", "blocked"]
    total_counts = {status: 0 for status in statuses}
    required_counts = {status: 0 for status in statuses}
    for row in rows:
        status = str(row.get("status", ""))
        if status not in total_counts:
            continue
        total_counts[status] += 1
        if str(row.get("required_for_submission", "")).lower() == "true":
            required_counts[status] += 1

    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    labels = ["All gates", "Required gates"]
    x_positions = [0, 1]
    width = 0.22
    colors = {"ready": "#2f6f8f", "partial": "#b8a04a", "blocked": "#b84a4a"}
    offsets = [-width, 0, width]
    for offset, status in zip(offsets, statuses):
        ax.bar(
            [x + offset for x in x_positions],
            [total_counts[status], required_counts[status]],
            width=width,
            color=colors[status],
            label=status.capitalize(),
        )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Gate count")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, out_dir, "paper2_readiness_audit")


def plot_dataset_compliance(path: Path, out_dir: Path) -> None:
    if not path.is_file():
        return
    with path.open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    statuses = ["ready", "partial", "blocked"]
    counts = {status: 0 for status in statuses}
    required_counts = {status: 0 for status in statuses}
    for row in rows:
        status = str(row.get("status", ""))
        if status not in counts:
            continue
        counts[status] += 1
        if str(row.get("required_for_submission", "")).lower() == "true":
            required_counts[status] += 1

    fig, ax = plt.subplots(figsize=(7.2, 4.2))
    labels = ["All datasets", "Required datasets"]
    x_positions = [0, 1]
    width = 0.22
    colors = {"ready": "#2f6f8f", "partial": "#b8a04a", "blocked": "#b84a4a"}
    for offset, status in zip([-width, 0, width], statuses):
        ax.bar(
            [x + offset for x in x_positions],
            [counts[status], required_counts[status]],
            width=width,
            color=colors[status],
            label=status.capitalize(),
        )
    ax.set_xticks(x_positions)
    ax.set_xticklabels(labels)
    ax.set_ylabel("Dataset count")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(frameon=False)
    _save(fig, out_dir, "paper2_dataset_compliance_audit")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--summary", type=Path, default=DEFAULT_RESULTS)
    parser.add_argument("--kg-propagation", type=Path, default=DEFAULT_KG_PROP)
    parser.add_argument("--graph-embedding", type=Path, default=DEFAULT_GRAPH_EMBED)
    parser.add_argument("--graph-attention", type=Path, default=DEFAULT_GRAPH_ATTENTION)
    parser.add_argument("--dataset-replay", type=Path, default=DEFAULT_DATASET_REPLAY)
    parser.add_argument("--fhir-replay", type=Path, default=DEFAULT_FHIR_REPLAY)
    parser.add_argument("--expert-review", type=Path, default=DEFAULT_EXPERT_REVIEW)
    parser.add_argument("--entity-map", type=Path, default=DEFAULT_ENTITY_MAP)
    parser.add_argument("--dataset-compliance", type=Path, default=DEFAULT_DATASET_COMPLIANCE)
    parser.add_argument("--readiness", type=Path, default=DEFAULT_READINESS)
    parser.add_argument("--out-dir", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    rows = _load_summary_rows(args.summary)
    plot_summary(rows, args.out_dir)
    plot_tradeoff(rows, args.out_dir)
    plot_kg_propagation(args.kg_propagation, args.out_dir)
    plot_graph_embedding(args.graph_embedding, args.out_dir)
    plot_graph_attention(args.graph_attention, args.out_dir)
    plot_dataset_replay(args.dataset_replay, args.out_dir)
    plot_fhir_validator_replay(args.fhir_replay, args.out_dir)
    plot_expert_review(args.expert_review, args.out_dir)
    plot_entity_map_coverage(args.entity_map, args.out_dir)
    plot_dataset_compliance(args.dataset_compliance, args.out_dir)
    plot_readiness_audit(args.readiness, args.out_dir)
    print(f"wrote figures to {args.out_dir}")


if __name__ == "__main__":
    main()
