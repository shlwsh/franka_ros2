#!/usr/bin/env python3
"""LaTeX table for Bbrisque / Bniqe appendix results."""

from __future__ import annotations

import csv
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latex_table_wrap import wrap_tabular

PAPER1_ROOT = Path(__file__).resolve().parents[2]
RESULTS = PAPER1_ROOT / 'experiments/results'


def mean_pm_std(xs: list[float], d: int = 1) -> str:
    m = statistics.mean(xs)
    if len(xs) < 2:
        return f'{m:.{d}f}'
    return f'{m:.{d}f} $\\pm$ {statistics.stdev(xs):.{d}f}'


def load_agg(tag: str = 'nr') -> dict:
    agg = defaultdict(lambda: {'p50': [], 'm2': [], 'm3': []})
    for seed in [0, 1, 2]:
        path = RESULTS / f'main_seed{seed}_nr.csv'
        if not path.is_file():
            suffix = f'_{tag}' if tag else ''
            path = RESULTS / f'main_seed{seed}{suffix}.csv'
        if not path.is_file():
            continue
        with path.open(encoding='utf-8') as f:
            for row in csv.DictReader(f):
                bl = row['baseline']
                agg[bl]['p50'].append(float(row['m1_p50_ms']))
                agg[bl]['m2'].append(float(row['m2_valid_rate']))
                agg[bl]['m3'].append(float(row['m3_retry_rate']))
    return agg


def write_table(out: Path, *, caption: str, label: str, header: str, baselines: list[str], agg: dict):
    lines_body = [r'\hline', header, r'\hline']
    for bl in baselines:
        a = agg[bl]
        lines_body.append(
            f'{bl} & {mean_pm_std(a["p50"])} & {mean_pm_std(a["m2"], 3)} & '
            f'{mean_pm_std(a["m3"], 3)} \\\\'
        )
    lines_body.append(r'\hline')
    text = [
        '% NR-IQA appendix table — auto-generated',
        r'\begin{table}[t]',
        r'\centering',
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}',
        *wrap_tabular('lccc', lines_body),
        r'\end{table}',
        '',
    ]
    out.write_text('\n'.join(text), encoding='utf-8')


def main() -> None:
    agg = load_agg('nr')
    if not agg:
        print('No NR results; run run_matrix_tcm.py --tag nr first')
        return
    write_table(
        PAPER1_ROOT / 'latex/sections/table_nr_iqa.tex',
        caption=(
            'Classical NR-IQA baselines with the same LangGraph resampling shell as B2 '
            r'(ShezhenV3 test, 500 frames $\times$ 3 seeds; $\tau$ from validation medians). '
            'Scores use validation-calibrated OpenCV BRISQUE (Bbrisque) and '
            'NSS Mahalanobis distance (Bniqe, NIQE-style) on tongue ROI crops.'
        ),
        label='tab:nr-iqa',
        header='Baseline & M1 p50 (ms) & M2 & M3 retry \\\\',
        baselines=['Bbrisque', 'Bniqe'],
        agg=agg,
    )
    write_table(
        PAPER1_ROOT / 'latex/sections/zh/table_nr_iqa.tex',
        caption=(
            '经典 NR-IQA 基线，与 B2 相同的 LangGraph 重采外壳（500 帧 $\times$ 3 seeds）。'
            'Bbrisque 为 OpenCV BRISQUE；Bniqe 为 NSS 马氏距离（NIQE 风格）。'
        ),
        label='tab:nr-iqa-zh',
        header='基线 & M1 p50 (ms) & M2 & M3 重拍率 \\\\',
        baselines=['Bbrisque', 'Bniqe'],
        agg=agg,
    )
    print('Wrote NR-IQA tables')


if __name__ == '__main__':
    main()
