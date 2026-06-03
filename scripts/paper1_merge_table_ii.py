#!/usr/bin/env python3
"""Rebuild table_ii.json from main_seed{0,1,2}.csv after partial matrix runs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PAPER1 = Path(__file__).resolve().parents[1] / 'doctor' / 'paper1'
RESULTS = PAPER1 / 'experiments' / 'results'


def main() -> int:
    rows: list[dict] = []
    seeds_found: list[int] = []
    for seed in [0, 1, 2]:
        path = RESULTS / f'main_seed{seed}.csv'
        if not path.is_file():
            continue
        with path.open(encoding='utf-8') as f:
            part = list(csv.DictReader(f))
        if len(part) < 6:
            print(f'WARN main_seed{seed}.csv has {len(part)} rows (expected 6 baselines)')
        rows.extend(part)
        seeds_found.append(seed)

    if not rows:
        raise SystemExit('no main_seed*.csv found')

    out = RESULTS / 'table_ii.json'
    out.write_text(json.dumps(rows, indent=2), encoding='utf-8')
    meta_path = RESULTS / 'table_ii_meta.json'
    meta = {}
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
    meta['seeds'] = seeds_found
    meta['n_rows'] = len(rows)
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'Merged {len(rows)} rows from seeds {seeds_found} -> {out}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
