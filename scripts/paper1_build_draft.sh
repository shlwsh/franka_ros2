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

echo "--- Chinese PDF (xelatex) ---"
if command -v xelatex >/dev/null; then
  set +e
  xelatex -interaction=nonstopmode main-zh.tex >/dev/null
  bibtex main-zh >/dev/null 2>&1
  xelatex -interaction=nonstopmode main-zh.tex >/dev/null
  xelatex -interaction=nonstopmode main-zh.tex >/dev/null
  set -e
  test -f main-zh.pdf
  echo "Chinese PDF: ${PAPER1_ROOT}/latex/main-zh.pdf ($(wc -c < main-zh.pdf) bytes)"
else
  echo "SKIP main-zh.pdf (install texlive-xetex)"
fi
