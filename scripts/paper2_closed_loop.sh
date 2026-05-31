#!/usr/bin/env bash
# Paper II synthetic closed-loop MVP.
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
TRIALS="${TRIALS:-24}"
LOG_PATH="${LOG_PATH:-${ROOT}/doctor/paper2/experiments/logs/paper2_run_001.jsonl}"

cd "$ROOT"
python3 -m doctor.paper2.langgraph_router.run \
  --trials "$TRIALS" \
  --log "$LOG_PATH"

python3 doctor/paper2/experiments/run_dataset_replay.py \
  --trials "$TRIALS" \
  --dataset-id sample_open_csv

python3 doctor/paper2/kg/export_edges.py
python3 doctor/paper2/kg/entity_map_coverage.py
python3 doctor/paper2/experiments/run_kg_propagation.py --trials "$TRIALS"
python3 doctor/paper2/experiments/run_graph_embedding.py --trials "$TRIALS"
python3 doctor/paper2/experiments/run_graph_attention.py --trials "$TRIALS"
python3 doctor/paper2/experiments/run_fhir_validation_replay.py --trials "$TRIALS"
python3 doctor/paper2/experiments/run_expert_review.py
python3 doctor/paper2/experiments/run_real_expert_review.py --write-template
python3 doctor/paper2/experiments/run_dataset_compliance_audit.py
python3 doctor/paper2/experiments/run_readiness_audit.py --skip-franka-probe
python3 doctor/paper2/figures/plot_results.py

wc -l "$LOG_PATH"
