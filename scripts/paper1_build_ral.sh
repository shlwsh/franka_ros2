#!/usr/bin/env bash
# Build RA-L submission PDF (IEEEtran, max 8 pages) + optional full archive PDF
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
export PAPER1_ROOT

cd "$PAPER1_ROOT/latex"

echo "=== RA-L manuscript (main-ral.pdf, IEEEtran, max 8 pages) ==="
pdflatex -interaction=nonstopmode main-ral.tex >/dev/null
bibtex main-ral >/dev/null 2>&1 || true
pdflatex -interaction=nonstopmode main-ral.tex >/dev/null
pdflatex -interaction=nonstopmode main-ral.tex >/dev/null
test -f main-ral.pdf

PAGES=$(pdfinfo main-ral.pdf | awk '/Pages:/ {print $2}')
echo "main-ral.pdf: ${PAGES} pages ($(wc -c < main-ral.pdf) bytes)"
if [ "$PAGES" -gt 8 ]; then
  echo "ERROR: RA-L limit is 8 pages; trim sections/ral/ or move content to supplementary/" >&2
  exit 1
fi

# Sync submission package
SUB="${PAPER1_ROOT}/submission/RA-L_20260529"
mkdir -p "$SUB"
cp main-ral.pdf "$SUB/manuscript.pdf"
cp references.bib "$SUB/references.bib"
echo "Synced -> ${SUB}/manuscript.pdf"

echo "=== Full archive (main.pdf, optional internal reference) ==="
if [ "${BUILD_FULL_ARCHIVE:-0}" = "1" ]; then
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  bibtex main >/dev/null 2>&1 || true
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  pdflatex -interaction=nonstopmode main.tex >/dev/null
  cp main.pdf "$SUB/manuscript-full-archive.pdf"
  echo "Archive: ${SUB}/manuscript-full-archive.pdf"
fi

echo "Done."
