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

    meta_path = PAPER1_ROOT / 'experiments/results/table_ii_meta.json'
    caption_extra = 'offline simulation, 3 seeds, 500 frames/baseline/seed'
    if meta_path.is_file():
        import json

        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        ds = meta.get('dataset', 'TCM')
        caption_extra = (
            f'{ds} test split, real Edge-IQA scores, 3 seeds, '
            f'{meta.get("n_test_images", 500)} images available'
        )

    lines = [
        '% Table II — auto-generated from main_seed*.csv',
        '\\begin{table}[t]',
        '\\centering',
        f'\\caption{{Main results ({caption_extra}; physical resample, $\\tau_{{B2}}$).}}',
        '\\label{tab:main-results}',
        '\\small',
        '\\resizebox{\\columnwidth}{!}{%',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        'Baseline & M1 p50 (ms) & M1 p95 (ms) & M2 valid rate & M3 retry rate \\\\',
        '\\hline',
    ]
    for bl in ['B0', 'B1', 'B2']:
        a = agg[bl]
        lines.append(
            f'{bl} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
        )
    lines.extend(['\\hline', '\\end{tabular}%', '}', '\\end{table}', ''])
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote', OUT)


if __name__ == '__main__':
    main()
