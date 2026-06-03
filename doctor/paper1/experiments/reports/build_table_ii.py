#!/usr/bin/env python3
"""Generate Table II LaTeX snippet from main_seed*.csv."""

from __future__ import annotations

import csv
import json
import statistics
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latex_table_wrap import wrap_tabular

PAPER1_ROOT = Path(__file__).resolve().parents[2]
OUT_EN = PAPER1_ROOT / 'latex/sections/table_ii.tex'
OUT_ZH = PAPER1_ROOT / 'latex/sections/zh/table_ii.tex'


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def mean_pm_std(xs: list[float], *, decimals: int = 1) -> str:
    m = mean(xs)
    if len(xs) < 2:
        return f'{m:.{decimals}f}'
    s = statistics.stdev(xs)
    return f'{m:.{decimals}f} $\\pm$ {s:.{decimals}f}'


def build_rows(agg: dict, baselines: list[str], header: str) -> list[str]:
    lines = [r'\hline', header, r'\hline']
    for bl in baselines:
        a = agg[bl]
        lines.append(
            f'{bl} & {mean_pm_std(a["p50"])} & {mean_pm_std(a["p95"])} & '
            f'{mean_pm_std(a["m2"], decimals=3)} & {mean_pm_std(a["m3"], decimals=3)} \\\\'
        )
    lines.append(r'\hline')
    return lines


def write_table(
    out: Path,
    *,
    caption: str,
    label: str,
    header: str,
    baselines: list[str],
    agg: dict,
) -> None:
    body = build_rows(agg, baselines, header)
    lines = [
        '% Table II — auto-generated from main_seed*.csv',
        r'\begin{table}[t]',
        r'\centering',
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}',
        *wrap_tabular('lcccc', body),
        r'\end{table}',
        '',
    ]
    out.write_text('\n'.join(lines), encoding='utf-8')


def bootstrap_footnote() -> str:
    path = PAPER1_ROOT / 'experiments/results/table_ii_bootstrap.json'
    if not path.is_file():
        return ''
    import json

    meta = json.loads(path.read_text(encoding='utf-8'))
    parts = []
    for bl in ['B0', 'B1', 'B2']:
        if bl not in meta:
            continue
        m = meta[bl]
        parts.append(
            f'{bl} M2={m["m2"]:.3f} [{m["ci_lo"]:.3f},{m["ci_hi"]:.3f}]'
        )
    if not parts:
        return ''
    return (
        ' Frame-level bootstrap 95\\% CIs for M2 (pooled over $3\\times500$ frames): '
        + '; '.join(parts)
        + '.'
    )


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

    n_test = 553
    meta_path = PAPER1_ROOT / 'experiments/results/table_ii_meta.json'
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        n_test = meta.get('n_test_images', n_test)

    boot = bootstrap_footnote()
    en_caption = (
        f'Main results (ShezhenV3 test, {n_test} images; Edge-IQA, '
        f'physical resample, $\\tau_{{B2}}$, 3 seeds). '
        f'Cells report mean $\\pm$ std over seeds.{boot}'
    )
    zh_boot = boot.replace('Frame-level bootstrap', '帧级 bootstrap').replace(
        'pooled over', '合并'
    )
    zh_caption = (
        f'主实验结果（ShezhenV3 测试集，{n_test} 张；真实 Edge-IQA，'
        f'物理重采，$\\tau_{{B2}}$，3 个随机种子）。'
        f'表中为各 seed 均值 $\\pm$ 标准差。{zh_boot}'
    )
    write_table(
        OUT_EN,
        caption=en_caption,
        label='tab:main-results',
        header='Baseline & M1 p50 (ms) & M1 p95 (ms) & M2 valid rate & M3 retry rate \\\\',
        baselines=['B0', 'B1', 'B2'],
        agg=agg,
    )
    write_table(
        OUT_ZH,
        caption=zh_caption,
        label='tab:main-results-zh',
        header='基线 & M1 p50 (ms) & M1 p95 (ms) & M2 有效帧率 & M3 重拍率 \\\\',
        baselines=['B0', 'B1', 'B2'],
        agg=agg,
    )
    print('Wrote', OUT_EN, 'and', OUT_ZH)


if __name__ == '__main__':
    main()
