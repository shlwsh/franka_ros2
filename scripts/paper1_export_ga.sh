#!/usr/bin/env bash
# Export RA-L Graphical Abstract PNG (1200x600) from SVG source.
set -eo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
SVG="${PAPER1_ROOT}/figures/graphical_abstract_ral.svg"
OUT="${PAPER1_ROOT}/submission/RA-L_20260529/graphical_abstract.png"

command -v rsvg-convert >/dev/null || { echo "Install: apt install librsvg2-bin" >&2; exit 1; }
test -f "$SVG"
rsvg-convert -w 1200 -h 600 "$SVG" -o "$OUT"
cp "$OUT" "${PAPER1_ROOT}/figures/graphical_abstract_ral.png"
echo "Wrote ${OUT} ($(python3 -c "from PIL import Image; print(Image.open('${OUT}').size)" 2>/dev/null || file -b "$OUT"))"
