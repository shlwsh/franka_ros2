#!/usr/bin/env bash
# 主轨离线实验：run_matrix → Fig.5/6 → Table II
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
export PAPER1_ROOT

cd "$PAPER1_ROOT"
python3 experiments/run_matrix.py --config experiments/configs/main_exp.yaml
python3 figures/plot_main.py
python3 experiments/reports/build_table_ii.py
echo "Main track done: ${PAPER1_ROOT}/experiments/results/main_seed*.csv"
