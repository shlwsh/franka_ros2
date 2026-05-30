#!/usr/bin/env bash
# Full Paper I validation on ShezhenV3-COCO (TCM tongue dataset)
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"

echo "=== [1/8] Import ShezhenV3 splits ==="
python3 scripts/import_shezhenv3.py

echo "=== [2/8] Calibrate tau on full val (clear + synthetic blur) ==="
python3 experiments/edge_iqa/calibrate_tau_tcm.py

echo "=== [3/8] M5 cross-cohort Spearman ==="
python3 experiments/cross_dataset_report.py

echo "=== [4/8] Main experiment matrix (TCM test, 3 seeds) ==="
python3 experiments/run_matrix_tcm.py

echo "=== [5/8] Tau ablation ==="
python3 experiments/run_ablation_tau.py 2>/dev/null || true

echo "=== [6/8] Figures + Table II ==="
python3 figures/plot_iqa_hist.py
python3 figures/plot_main.py
python3 experiments/reports/build_table_ii.py

echo "=== [7/8] LaTeX tables (dataset, tongue, zh sync) ==="
python3 experiments/reports/build_dataset_tables.py
python3 experiments/reports/build_tongue_table.py
python3 experiments/reports/sync_table_ii_zh.py

echo "=== [8/8] Build LaTeX PDFs ==="
bash "$ROOT/scripts/paper1_build_draft.sh"

echo "Done. Results: experiments/results/  Figures: figures/  PDF: latex/main.pdf"
