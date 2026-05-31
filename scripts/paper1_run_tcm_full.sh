#!/usr/bin/env bash
# Full Paper I validation on ShezhenV3-COCO (TCM tongue dataset)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"
mkdir -p experiments/logs

# shellcheck source=paper1_log_lib.sh
source "$ROOT/scripts/paper1_log_lib.sh"
paper1_log_init "experiments/logs/tcm_full_run.log"

# Avoid bash expanding $edg inside edge_iqa — always use quoted paths.
readonly EDGE_IQA_DIR='experiments/edge_iqa'
readonly PY_SYS='python3'
readonly PY_VENV='.venv/bin/python'
readonly B3_CKPT='experiments/results/b3_mobilenet.pt'

export PAPER1_TRACE="${PAPER1_TRACE:-1}"
export PAPER1_TRACE_FRAMES="${PAPER1_TRACE_FRAMES:-0}"

paper1_run_step '1/10' 'Import ShezhenV3 splits' \
  paper1_run_python "$PY_SYS" scripts/import_shezhenv3.py

if [[ ! -f "$B3_CKPT" ]]; then
  paper1_run_step '2/10' 'Train B3 MobileNet' \
    paper1_run_python "$PY_VENV" "${EDGE_IQA_DIR}/train_b3_mobilenet.py"
else
  paper1_log_info 'SKIP step 2/10 B3 training (checkpoint exists)'
fi

paper1_run_step '3a/10' 'Calibrate tau_B2 (Edge-IQA)' \
  paper1_run_python "$PY_SYS" "${EDGE_IQA_DIR}/calibrate_tau_tcm.py"

paper1_run_step '3b/10' 'Calibrate tau_B3 (MobileNet)' \
  paper1_run_python "$PY_VENV" "${EDGE_IQA_DIR}/calibrate_tau_b3.py"

paper1_run_step '4/10' 'ROI ablation' \
  paper1_run_python "$PY_SYS" "${EDGE_IQA_DIR}/roi_ablation.py"

paper1_run_step '5/10' 'M5 cross-cohort Spearman' \
  paper1_run_python "$PY_SYS" experiments/cross_dataset_report.py

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

paper1_log_info 'Pipeline complete. Results: experiments/results/  Figures: figures/  PDF: latex/main.pdf'
