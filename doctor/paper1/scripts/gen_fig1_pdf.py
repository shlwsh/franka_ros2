#!/usr/bin/env python3
"""Generate fig1_system_overview.pdf from SVG (optional, requires cairosvg)."""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SVG = ROOT / 'figures' / 'fig1_system_overview.svg'
PDF = ROOT / 'figures' / 'fig1_system_overview.pdf'


def main() -> None:
    try:
        import cairosvg
    except ImportError:
        print('cairosvg not installed; keep SVG only:', SVG)
        return
    cairosvg.svg2pdf(url=str(SVG), write_to=str(PDF))
    print('Wrote', PDF)


if __name__ == '__main__':
    main()
