# Paper II Research MVP

This directory contains a reproducible software MVP for Paper II:
knowledge-gated multi-agent conflict realignment with optional embodied
resampling through the existing `franka_api_server` tool surface.

The current implementation is intentionally synthetic and dependency-light. It
does not use real clinical records, PHI, external LLM calls, or restricted
medical ontologies. Its purpose is to produce traceable JSONL/CSV evidence for
the first bilingual Paper II draft.

## Quick Run

From the repository root:

```bash
python3 -m doctor.paper2.langgraph_router.run --trials 24
```

See `REPRODUCE.md` for the complete test, run, and LaTeX build sequence.

Outputs:

- `doctor/paper2/experiments/logs/paper2_run_001.jsonl`
- `doctor/paper2/experiments/results/paper2_summary.csv`
- `doctor/paper2/experiments/results/conflict_detection.csv`
- `doctor/paper2/experiments/results/fhir_validation.csv`
- `doctor/paper2/experiments/results/resample.csv`
- `doctor/paper2/experiments/results/tool_ablation.csv`
- `doctor/paper2/experiments/reports/paper2_mvp_report.md`
- `doctor/paper2/figures/paper2_summary_metrics.svg`
- `doctor/paper2/figures/paper2_hallucination_fhir_tradeoff.svg`
- `doctor/paper2/figures/paper2_kg_propagation_scores.svg`
- `doctor/paper2/figures/paper2_graph_embedding_scores.svg`
- `doctor/paper2/kg/kg_edges.csv`
- `doctor/paper2/experiments/results/kg_propagation.csv`
- `doctor/paper2/experiments/reports/kg_propagation_report.md`
- `doctor/paper2/experiments/results/graph_embedding.csv`
- `doctor/paper2/experiments/reports/graph_embedding_report.md`
- `doctor/paper2/experiments/results/graph_attention.csv`
- `doctor/paper2/experiments/reports/graph_attention_report.md`
- `doctor/paper2/figures/paper2_graph_attention_scores.svg`
- `doctor/paper2/datasets/registry.json`
- `doctor/paper2/datasets/samples/paper2_cases.sample.csv`
- `doctor/paper2/experiments/results/dataset_replay.csv`
- `doctor/paper2/experiments/reports/dataset_replay_report.md`
- `doctor/paper2/figures/paper2_dataset_replay_rates.svg`
- `doctor/paper2/experiments/results/dataset_compliance_audit.csv`
- `doctor/paper2/experiments/reports/dataset_compliance_audit_report.md`
- `doctor/paper2/figures/paper2_dataset_compliance_audit.svg`
- `doctor/paper2/experiments/results/fhir_validator_replay.csv`
- `doctor/paper2/experiments/reports/fhir_validator_replay_report.md`
- `doctor/paper2/figures/paper2_fhir_validator_replay.svg`
- `doctor/paper2/kg/entity_map.csv`
- `doctor/paper2/kg/ONTOLOGY_LICENSE_NOTES.md`
- `doctor/paper2/experiments/results/entity_map_coverage.csv`
- `doctor/paper2/experiments/reports/entity_map_coverage_report.md`
- `doctor/paper2/figures/paper2_entity_map_coverage.svg`
- `doctor/paper2/experiments/expert_review/PROTOCOL.md`
- `doctor/paper2/experiments/expert_review/review_packet.csv`
- `doctor/paper2/experiments/expert_review/real_annotations.template.csv`
- `doctor/paper2/experiments/results/expert_review_agreement.csv`
- `doctor/paper2/experiments/reports/expert_review_protocol_report.md`
- `doctor/paper2/figures/paper2_expert_review_agreement.svg`
- `doctor/paper2/experiments/run_real_expert_review.py`
- `doctor/paper2/experiments/results/readiness_audit.csv`
- `doctor/paper2/experiments/reports/readiness_audit_report.md`
- `doctor/paper2/figures/paper2_readiness_audit.svg`
- `doctor/paper2/tools/fhir_validator.py`
- `doctor/paper2/tools/franka_probe.py`
- `docs-zh/paper2/论文II_中文稿_20260531.md`
- `docs-zh/paper2/PaperII_English_Draft_20260531.md`
- `doctor/paper2/latex/main-zh.tex`
- `doctor/paper2/latex/main.tex`
- `doctor/paper2/latex/main-zh.pdf`
- `doctor/paper2/latex/main.pdf`

## Scope

- `doctor/paper2`: cognition/research layer, synthetic experiments, manuscript evidence.
- `franka_api_server`: existing edge/tool layer, called optionally through HTTP.
- `franka_*`: existing ROS 2 device layer.

Do not commit passwords, API keys, clinical data, or restricted ontology dumps.
