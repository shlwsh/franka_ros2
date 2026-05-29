#!/usr/bin/env python3
"""Generate Table II LaTeX snippet from main_seed*.csv."""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
OUT = PAPER1_ROOT / 'latex/sections/table_ii.tex'


def main() -> None:
    agg: dict = defaultdict(lambda: {'p50': [], 'p95': [], 'm2': [], 'm3': []})
    for seed in [0, 1, 2]:
        path = PAPER1_ROOT / 'experiments/results' / f'main_seed{seed}.csv'
        with path.open(encoding='utf-8') as f:
            for row in csv.DictReader(f):
                bl = row['baseline']
                agg[bl]['p50'].append(float(row['m1_p50_ms']))
                agg[bl]['p95'].append(float(row['m1_p95_ms']))
                agg[bl]['m2'].append(float(row['m2_valid_rate']))
                agg[bl]['m3'].append(float(row['m3_retry_rate']))

    def mean(xs):
        return sum(xs) / len(xs)

    lines = [
        '% Table II — auto-generated from main_seed*.csv',
        '\\begin{table}[t]',
        '\\centering',
        '\\caption{Main results (offline simulation, 3 seeds, 500 frames/baseline/seed).}',
        '\\label{tab:main-results}',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        'Baseline & M1 p50 (ms) & M1 p95 (ms) & M2 valid rate & M3 retry rate \\\\',
        '\\hline',
    ]
    for bl in ['B0', 'B1', 'B2', 'B3']:
        a = agg[bl]
        lines.append(
            f'{bl} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
        )
    lines.extend(['\\hline', '\\end{tabular}', '\\end{table}', ''])
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote', OUT)


if __name__ == '__main__':
    main()
