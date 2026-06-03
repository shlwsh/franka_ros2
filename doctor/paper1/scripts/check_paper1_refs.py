#!/usr/bin/env python3
"""Check \\label / \\ref consistency under doctor/paper1/latex/sections."""

from __future__ import annotations

import re
import sys
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[1]
SECTIONS = [
    PAPER1_ROOT / 'latex',
    PAPER1_ROOT / 'latex/sections',
    PAPER1_ROOT / 'latex/sections/zh',
]

LABEL_RE = re.compile(r'\\label\{([^}]+)\}')
REF_RE = re.compile(r'\\ref\{([^}]+)\}')


def collect_tex(paths: list[Path]) -> str:
    chunks: list[str] = []
    for p in sorted(paths):
        if p.suffix == '.tex':
            chunks.append(p.read_text(encoding='utf-8', errors='replace'))
    return '\n'.join(chunks)


def main() -> int:
    tex_files = []
    for root in SECTIONS:
        if root.is_dir():
            tex_files.extend(root.rglob('*.tex'))
    text = collect_tex(tex_files)
    labels = set(LABEL_RE.findall(text))
    refs = set(REF_RE.findall(text))
    missing = sorted(refs - labels)
    unused = sorted(labels - refs)

    print(f'Labels: {len(labels)}, Refs: {len(refs)}')
    if missing:
        print('\nMISSING labels for refs:')
        for m in missing:
            print('  -', m)
    if unused:
        print(f'\nUnused labels ({len(unused)}): showing up to 20')
        for u in unused[:20]:
            print('  -', u)
    return 1 if missing else 0


if __name__ == '__main__':
    sys.exit(main())
