#!/usr/bin/env bash
# 阶段 5：消融 + 跨集 + LaTeX main.pdf
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
export PAPER1_ROOT

cd "$PAPER1_ROOT"
python3 experiments/run_ablation_tau.py
python3 figures/plot_ablation_tau.py
python3 experiments/cross_dataset_report.py 2>/dev/null || true

cd latex
set +e
pdflatex -interaction=nonstopmode main.tex >/dev/null
bibtex main >/dev/null 2>&1
pdflatex -interaction=nonstopmode main.tex >/dev/null
pdflatex -interaction=nonstopmode main.tex >/dev/null
set -e
test -f main.pdf
echo "Draft PDF: ${PAPER1_ROOT}/latex/main.pdf ($(wc -c < main.pdf) bytes)"
