#!/usr/bin/env bash
# Resume from step 6 (steps 1-5 assumed done: import, tau, ROI, M5).
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"
mkdir -p experiments/logs

# shellcheck source=paper1_log_lib.sh
source "$ROOT/scripts/paper1_log_lib.sh"
paper1_log_init "experiments/logs/tcm_full_resume.log"

readonly PY_SYS='python3'
readonly PY_VENV='.venv/bin/python'

export PAPER1_TRACE="${PAPER1_TRACE:-1}"
export PAPER1_TRACE_FRAMES="${PAPER1_TRACE_FRAMES:-0}"

paper1_log_info 'RESUME from step 6/10 (import + tau + ROI + M5 assumed done)'

paper1_run_step '6/10' 'Main matrix (TCM test, 3 seeds)' \
  paper1_run_python "$PY_VENV" experiments/run_matrix_tcm.py

paper1_run_step '7/10' 'Tau ablation (optional)' \
  paper1_run_python "$PY_SYS" experiments/run_ablation_tau.py || paper1_log_info 'Tau ablation skipped (non-fatal)'

paper1_run_step '8a/10' 'Plot IQA histogram' \
  paper1_run_python "$PY_SYS" figures/plot_iqa_hist.py

paper1_run_step '8b/10' 'Plot main figures' \
  paper1_run_python "$PY_SYS" figures/plot_main.py

paper1_run_step '8c/10' 'Build Table II' \
  paper1_run_python "$PY_SYS" experiments/reports/build_table_ii.py

paper1_run_step '8d/10' 'Build Table III' \
  paper1_run_python "$PY_SYS" experiments/reports/build_table_iii.py

paper1_run_step '9a/10' 'Build dataset tables' \
  paper1_run_python "$PY_SYS" experiments/reports/build_dataset_tables.py

paper1_run_step '9b/10' 'Build tongue table' \
  paper1_run_python "$PY_SYS" experiments/reports/build_tongue_table.py

paper1_run_step '9c/10' 'Sync Table II zh' \
  paper1_run_python "$PY_SYS" experiments/reports/sync_table_ii_zh.py

paper1_run_step '10/10' 'Build LaTeX PDFs' \
  bash "$ROOT/scripts/paper1_build_draft.sh"

paper1_log_info 'Resume pipeline complete.'
