#!/usr/bin/env bash
# M6 辅轨：50 trial 闭环 RTT → franka_m6_rtt.csv
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
TRIALS="${TRIALS:-50}"
JSONL="${PAPER1_ROOT}/experiments/logs/m6_run.jsonl"

export PAPER1_ROOT
cd "$ROOT"

if [[ ! -f "${PAPER1_ROOT}/experiments/synthetic/clear/clear_0000.png" ]]; then
  python3 "${PAPER1_ROOT}/scripts/synth_degrade.py"
fi

rm -f "$JSONL"
cd "$PAPER1_ROOT"
python3 -m langgraph_router.run --trials "$TRIALS" --log "$JSONL"

python3 "${PAPER1_ROOT}/experiments/summarize_m6.py" "$JSONL"
python3 "${PAPER1_ROOT}/figures/plot_m6_rtt.py"
python3 "${PAPER1_ROOT}/experiments/reports/build_m6_trend.py" 2>/dev/null || true

echo "M6 complete: ${PAPER1_ROOT}/experiments/results/franka_m6_rtt.csv"
