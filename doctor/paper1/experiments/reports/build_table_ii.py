#!/usr/bin/env python3
"""Generate Table II LaTeX snippet from main_seed*.csv."""

from __future__ import annotations

import csv
import json
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


def build_rows(agg: dict, baselines: list[str], header: str) -> list[str]:
    lines = [r'\hline', header, r'\hline']
    for bl in baselines:
        a = agg[bl]
        lines.append(
            f'{bl} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
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

    en_caption = (
        f'Main results (ShezhenV3 test, {n_test} images; Edge-IQA, '
        f'physical resample, $\\tau_{{B2}}$, 3 seeds).'
    )
    zh_caption = (
        f'主实验结果（ShezhenV3 测试集，{n_test} 张；真实 Edge-IQA，'
        f'物理重采，$\\tau_{{B2}}$，3 个随机种子）。'
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
