# Reproduce Paper II MVP

This file reproduces the current Paper II synthetic MVP and bilingual draft
artifacts. Run all commands from the repository root unless noted otherwise.

## 1. Run Tests

```bash
python3 -m pytest doctor/paper2/tests -q
```

Expected:

```text
46 passed
```

## 2. Run Synthetic Closed Loop

```bash
scripts/paper2_closed_loop.sh
```

Expected:

```text
120 .../doctor/paper2/experiments/logs/paper2_run_001.jsonl
```

Generated result files:

- `doctor/paper2/experiments/results/paper2_summary.csv`
- `doctor/paper2/experiments/results/conflict_detection.csv`
- `doctor/paper2/experiments/results/fhir_validation.csv`
- `doctor/paper2/experiments/results/fhir_validator_replay.csv`
- `doctor/paper2/experiments/results/expert_review_agreement.csv`
- `doctor/paper2/experiments/results/entity_map_coverage.csv`
- `doctor/paper2/experiments/results/dataset_compliance_audit.csv`
- `doctor/paper2/experiments/results/readiness_audit.csv`
- `doctor/paper2/experiments/results/resample.csv`
- `doctor/paper2/experiments/results/tool_ablation.csv`
- `doctor/paper2/experiments/results/closed_loop_latency.csv`
- `doctor/paper2/experiments/results/dataset_replay.csv`
- `doctor/paper2/experiments/reports/paper2_mvp_report.md`
- `doctor/paper2/experiments/reports/fhir_validator_replay_report.md`
- `doctor/paper2/experiments/reports/expert_review_protocol_report.md`
- `doctor/paper2/experiments/reports/entity_map_coverage_report.md`
- `doctor/paper2/experiments/reports/dataset_compliance_audit_report.md`
- `doctor/paper2/experiments/reports/readiness_audit_report.md`
- `doctor/paper2/experiments/reports/dataset_replay_report.md`

## 3. Generate Figures

```bash
python3 doctor/paper2/figures/plot_results.py
```

Generated figure files:

- `doctor/paper2/figures/paper2_summary_metrics.svg`
- `doctor/paper2/figures/paper2_summary_metrics.pdf`
- `doctor/paper2/figures/paper2_hallucination_fhir_tradeoff.svg`
- `doctor/paper2/figures/paper2_hallucination_fhir_tradeoff.pdf`
- `doctor/paper2/figures/paper2_kg_propagation_scores.svg`
- `doctor/paper2/figures/paper2_kg_propagation_scores.pdf`
- `doctor/paper2/figures/paper2_graph_embedding_scores.svg`
- `doctor/paper2/figures/paper2_graph_embedding_scores.pdf`
- `doctor/paper2/figures/paper2_graph_attention_scores.svg`
- `doctor/paper2/figures/paper2_graph_attention_scores.pdf`
- `doctor/paper2/figures/paper2_dataset_replay_rates.svg`
- `doctor/paper2/figures/paper2_dataset_replay_rates.pdf`
- `doctor/paper2/figures/paper2_dataset_compliance_audit.svg`
- `doctor/paper2/figures/paper2_dataset_compliance_audit.pdf`
- `doctor/paper2/figures/paper2_fhir_validator_replay.svg`
- `doctor/paper2/figures/paper2_fhir_validator_replay.pdf`
- `doctor/paper2/figures/paper2_expert_review_agreement.svg`
- `doctor/paper2/figures/paper2_expert_review_agreement.pdf`
- `doctor/paper2/figures/paper2_entity_map_coverage.svg`
- `doctor/paper2/figures/paper2_entity_map_coverage.pdf`
- `doctor/paper2/figures/paper2_readiness_audit.svg`
- `doctor/paper2/figures/paper2_readiness_audit.pdf`

## 4. Export KG Edges and Run Propagation Ablation

```bash
python3 doctor/paper2/kg/export_edges.py
python3 doctor/paper2/kg/entity_map_coverage.py
python3 doctor/paper2/experiments/run_kg_propagation.py --trials 24
python3 doctor/paper2/experiments/run_graph_embedding.py --trials 24
python3 doctor/paper2/experiments/run_graph_attention.py --trials 24
```

Generated KG evidence:

- `doctor/paper2/kg/kg_edges.csv`
- `doctor/paper2/kg/entity_map.csv`
- `doctor/paper2/kg/ONTOLOGY_LICENSE_NOTES.md`
- `doctor/paper2/experiments/results/entity_map_coverage.csv`
- `doctor/paper2/experiments/reports/entity_map_coverage_report.md`
- `doctor/paper2/experiments/results/kg_propagation.csv`
- `doctor/paper2/experiments/reports/kg_propagation_report.md`
- `doctor/paper2/experiments/results/graph_embedding.csv`
- `doctor/paper2/experiments/reports/graph_embedding_report.md`
- `doctor/paper2/experiments/results/graph_attention.csv`
- `doctor/paper2/experiments/reports/graph_attention_report.md`

## 5. Run Dataset Replay Bridge

The repository includes only no-PHI synthetic fixtures. The dataset registry
records open fixtures and controlled placeholders without committing clinical
records:

```bash
python3 doctor/paper2/experiments/run_dataset_replay.py --trials 24 --dataset-id sample_open_csv
```

Generated dataset evidence:

- `doctor/paper2/datasets/registry.json`
- `doctor/paper2/datasets/samples/paper2_cases.sample.csv`
- `doctor/paper2/experiments/results/dataset_replay.csv`
- `doctor/paper2/experiments/results/dataset_replay/paper2_summary.csv`
- `doctor/paper2/experiments/reports/dataset_replay_report.md`

Controlled placeholders such as `mimic_iv_note_placeholder` and
`mimic_cxr_placeholder` intentionally fail unless `--allow-controlled` is
provided and a local derived file exists. Source clinical records, PHI, and raw
controlled data must stay outside the repository.

Audit registry entries and derived case files before using any dataset as main
evidence:

```bash
python3 doctor/paper2/experiments/run_dataset_compliance_audit.py
```

Generated compliance evidence:

- `doctor/paper2/experiments/results/dataset_compliance_audit.csv`
- `doctor/paper2/experiments/reports/dataset_compliance_audit_report.md`
- `doctor/paper2/figures/paper2_dataset_compliance_audit.svg`

## 6. Batch FHIR Validator Replay

The MVP exports generated Bundle JSON artifacts and validates them with the
same adapter used by the closed loop:

```bash
python3 doctor/paper2/experiments/run_fhir_validation_replay.py --trials 24
```

Generated FHIR evidence:

- `doctor/paper2/experiments/fhir_bundles/`
- `doctor/paper2/experiments/results/fhir_validator_replay.csv`
- `doctor/paper2/experiments/reports/fhir_validator_replay_report.md`

By default the mode is `local-structural`. Set `PAPER2_FHIR_VALIDATOR_CMD` to
replay the same exported Bundles through an external validator CLI.

## 7. Optional FHIR Validator and API Readiness Probe

The MVP uses a deterministic local FHIR structural validator by default. To
wire a real validator CLI, provide a command template:

```bash
export PAPER2_FHIR_VALIDATOR_CMD='java -jar validator_cli.jar {path} -version 4.0.1'
```

The `{path}` placeholder is replaced with a temporary Bundle JSON file.

Probe the existing `franka_api_server` tool surface without requiring the
synthetic MVP to fail when ROS/API is offline:

```bash
python3 -m doctor.paper2.tools.franka_probe --timeout-s 3
```

The probe reports `online`, `partial`, or `offline` plus endpoint errors.

The full JSONL log is under `experiments/logs/`, which is ignored by the
repository. A small reviewable sample is tracked at:

- `doctor/paper2/experiments/samples/paper2_run_001.sample.jsonl`

## 8. Build Expert Review Protocol Packet

The tracked annotations are synthetic placeholders. They validate the blinded
review schema and agreement statistics, but they are not real physician review:

```bash
python3 doctor/paper2/experiments/run_expert_review.py
```

Generated review protocol evidence:

- `doctor/paper2/experiments/expert_review/PROTOCOL.md`
- `doctor/paper2/experiments/expert_review/review_packet.csv`
- `doctor/paper2/experiments/expert_review/synthetic_annotations.csv`
- `doctor/paper2/experiments/results/expert_review_agreement.csv`
- `doctor/paper2/experiments/reports/expert_review_protocol_report.md`

To prepare real expert annotation, write an empty template from the current
review packet:

```bash
python3 doctor/paper2/experiments/run_real_expert_review.py --write-template
```

After at least two real reviewers complete the template, validate it with:

```bash
python3 doctor/paper2/experiments/run_real_expert_review.py \
  --annotations doctor/paper2/experiments/expert_review/real_annotations.csv
```

Generated real-review evidence, once real annotations exist:

- `doctor/paper2/experiments/expert_review/real_annotations.template.csv`
- `doctor/paper2/experiments/expert_review/real_annotations.csv`
- `doctor/paper2/experiments/results/real_expert_review_agreement.csv`
- `doctor/paper2/experiments/reports/real_expert_review_report.md`

## 9. Run Submission Readiness Audit

The readiness audit is a conservative evidence gate. It records which software
fixtures are ready and which submission-critical requirements still lack
external evidence:

```bash
python3 doctor/paper2/experiments/run_readiness_audit.py --skip-franka-probe
```

Generated readiness evidence:

- `doctor/paper2/experiments/results/readiness_audit.csv`
- `doctor/paper2/experiments/reports/readiness_audit_report.md`
- `doctor/paper2/figures/paper2_readiness_audit.svg`

The default `--skip-franka-probe` form is deterministic for offline
reproduction. For real API/Gazebo/FR3 evidence, rerun without the skip flag
after starting `franka_api_server`.

## 10. Build Bilingual LaTeX Drafts

```bash
cd doctor/paper2/latex
pdflatex -interaction=nonstopmode main.tex
xelatex -interaction=nonstopmode main-zh.tex
```

Generated PDFs:

- `doctor/paper2/latex/main.pdf`
- `doctor/paper2/latex/main-zh.pdf`

## 11. Read Bilingual Markdown Drafts

- `docs-zh/paper2/PaperII_English_Draft_20260531.md`
- `docs-zh/paper2/论文II_中文稿_20260531.md`

## 12. Current Scientific Scope

The current MVP is synthetic. It does not use real clinical records, PHI,
external LLM calls, or restricted ontology dumps. It proves the executable
pipeline and evidence tracking only.

Remaining work for a submission-grade paper:

- replace synthetic cases with licensed public/controlled datasets;
- run and report an official external FHIR validator on the exported Bundles;
- replace placeholder-only ontology mappings with license-approved identifiers;
- scale the trainable graph-attention-lite baseline into a real GNN/GAT over licensed ontologies;
- run API/Gazebo/FR3 closed-loop experiments;
- replace synthetic reviewer placeholders with real expert review.
