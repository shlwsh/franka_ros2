#!/usr/bin/env python3
"""Build tables/figures for Paper I action-list items (bootstrap, stratified M2, Pareto)."""

from __future__ import annotations

import csv
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latex_table_wrap import wrap_tabular

PAPER1_ROOT = Path(__file__).resolve().parents[2]
RESULTS = PAPER1_ROOT / 'experiments/results'
FIGURES = PAPER1_ROOT / 'figures'


def bootstrap_ci(values: list[int], n_boot: int = 2000, alpha: float = 0.05) -> tuple[float, float, float]:
    if not values:
        return 0.0, 0.0, 0.0
    rng = random.Random(42)
    n = len(values)
    means = []
    for _ in range(n_boot):
        sample = [values[rng.randrange(n)] for _ in range(n)]
        means.append(sum(sample) / n)
    means.sort()
    lo = means[int((alpha / 2) * n_boot)]
    hi = means[int((1 - alpha / 2) * n_boot) - 1]
    return sum(values) / n, lo, hi


def build_bootstrap_footnote() -> dict:
    """Frame-level bootstrap on M2 (valid bit) pooled over 3 seeds."""
    out = {}
    for bl in ['B0', 'B1', 'B2']:
        vals = []
        for seed in [0, 1, 2]:
            path = RESULTS / f'main_seed{seed}_detail.csv'
            with path.open(encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if row['baseline'] == bl:
                        vals.append(int(row['valid']))
        m, lo, hi = bootstrap_ci(vals)
        out[bl] = {'m2': m, 'ci_lo': lo, 'ci_hi': hi, 'n': len(vals)}
    return out


def write_stratified_table() -> None:
    rows_en = []
    rows_zh = []
    for bl in ['B0', 'B2']:
        clear_v, blur_v = [], []
        for seed in [0, 1, 2]:
            path = RESULTS / f'main_seed{seed}_detail.csv'
            with path.open(encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if row['baseline'] != bl:
                        continue
                    if int(row.get('degraded', 0)):
                        blur_v.append(int(row['valid']))
                    else:
                        clear_v.append(int(row['valid']))
        m2c = sum(clear_v) / len(clear_v) if clear_v else 0
        m2b = sum(blur_v) / len(blur_v) if blur_v else 0
        rows_en.append(
            f'{bl} & {m2c:.3f} ({len(clear_v)} frames) & {m2b:.3f} ({len(blur_v)} frames) \\\\'
        )
        rows_zh.append(
            f'{bl} & {m2c:.3f}（{len(clear_v)} 帧） & {m2b:.3f}（{len(blur_v)} 帧） \\\\'
        )

    def pack(caption, label, header, body, out):
        lines = [
            '% auto-generated stratified M2',
            r'\begin{table}[t]',
            r'\centering',
            f'\\caption{{{caption}}}',
            f'\\label{{{label}}}',
            r'\small',
            r'\resizebox{\columnwidth}{!}{%',
            r'\begin{tabular}{lcc}',
            r'\hline',
            header,
            r'\hline',
            *body,
            r'\hline',
            r'\end{tabular}%',
            '}',
            r'\end{table}',
            '',
        ]
        out.write_text('\n'.join(lines), encoding='utf-8')

    pack(
        r'Stratified M2 (valid-frame rate) by injection cohort; pooled over 3 seeds $\times$ 500 frames.',
        'tab:stratified-m2',
        'Baseline & M2 (clear-source) & M2 (blur-injected) \\\\',
        rows_en,
        PAPER1_ROOT / 'latex/sections/table_stratified_m2.tex',
    )
    pack(
        '按注入类型分层的 M2（有效帧率）；3 个种子 $\times$ 500 帧合并统计。',
        'tab:stratified-m2-zh',
        '基线 & M2（清晰源） & M2（模糊注入） \\\\',
        rows_zh,
        PAPER1_ROOT / 'latex/sections/zh/table_stratified_m2.tex',
    )
    print('Wrote stratified M2 tables')


def plot_pareto() -> None:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt

    data = json.loads((RESULTS / 'table_ii.json').read_text(encoding='utf-8'))
    agg: dict = defaultdict(lambda: {'p50': [], 'm2': []})
    for row in data:
        bl = row['baseline']
        agg[bl]['p50'].append(float(row['m1_p50_ms']))
        agg[bl]['m2'].append(float(row['m2_valid_rate']))

    points = []
    for bl in ['B0', 'B1', 'B2', 'B3', 'B4']:
        if bl not in agg:
            continue
        points.append(
            (
                bl,
                statistics.mean(agg[bl]['p50']),
                statistics.mean(agg[bl]['m2']),
            )
        )

    fig, ax = plt.subplots(figsize=(5.5, 4))
    for bl, p50, m2 in points:
        ax.scatter(p50, m2, s=120, label=bl)
        ax.annotate(bl, (p50, m2), textcoords='offset points', xytext=(6, 4), fontsize=9)
    ax.set_xlabel('M1 RTT p50 (ms, simulated)')
    ax.set_ylabel('M2 valid-frame rate')
    ax.set_title('M2--M1 trade-off (ShezhenV3, 3 seeds)')
    ax.grid(True, alpha=0.3)
    ax.legend(loc='lower right', fontsize=8)
    fig.tight_layout()
    out = FIGURES / 'fig7_pareto_m2_m1.pdf'
    fig.savefig(out)
    print('Wrote', out)


def plot_failure_schematic() -> None:
    import matplotlib

    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np

    fig, axes = plt.subplots(1, 2, figsize=(6.5, 3))
    rng = np.random.default_rng(7)
    for ax, title, blur in zip(axes, ['Clear ROI (pass)', 'Blur-injected (fail)'], [False, True]):
        base = rng.random((64, 96))
        base = np.clip(base * 0.4 + 0.45, 0, 1)
        if blur:
            from scipy.ndimage import gaussian_filter

            base = gaussian_filter(base, sigma=2.2)
        ax.imshow(base, cmap='pink', aspect='auto')
        ax.set_title(title, fontsize=9)
        ax.axis('off')
    fig.suptitle('Illustrative ShezhenV3 tongue ROI crops (de-identified schematic)', fontsize=9)
    fig.tight_layout()
    out = FIGURES / 'fig_failure_modes_schematic.pdf'
    fig.savefig(out)
    print('Wrote', out)


def write_bootstrap_meta() -> None:
    meta = build_bootstrap_footnote()
    path = RESULTS / 'table_ii_bootstrap.json'
    path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print('Wrote', path, meta)


def main() -> None:
    write_bootstrap_meta()
    write_stratified_table()
    plot_pareto()
    try:
        plot_failure_schematic()
    except ImportError:
        print('SKIP failure schematic (scipy missing)')


if __name__ == '__main__':
    main()
