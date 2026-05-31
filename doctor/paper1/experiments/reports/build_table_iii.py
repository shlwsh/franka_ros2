#!/usr/bin/env python3
"""Generate Table III LaTeX (learned IQA + hybrid) from main_seed*.csv."""

from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
OUT_EN = PAPER1_ROOT / 'latex/sections/table_iii.tex'
OUT_ZH = PAPER1_ROOT / 'latex/sections/zh/table_iii.tex'


def mean(xs: list[float]) -> float:
    return sum(xs) / len(xs)


def build_rows(agg: dict, baselines: list[str]) -> list[str]:
    lines = []
    for bl in baselines:
        if bl not in agg:
            continue
        a = agg[bl]
        lines.append(
            f'{bl} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
        )
    return lines


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

    meta_path = PAPER1_ROOT / 'experiments/results/table_ii_meta.json'
    tau_b2 = tau_b3 = '?'
    if meta_path.is_file():
        meta = json.loads(meta_path.read_text(encoding='utf-8'))
        tau_b2 = meta.get('tau_b2', meta.get('tau', '?'))
        tau_b3 = meta.get('tau_b3', '?')

    label_map = {
        'B3': f'B3 (MobileNet, $\\tau_{{B2}}$={tau_b2})',
        'B3t': f'B3 (MobileNet, $\\tau_{{B3}}$={tau_b3})',
        'B4': 'B4 (Hybrid Tier-A/B)',
    }
    zh_map = {
        'B3': f'B3（MobileNet，$\\tau_{{B2}}$={tau_b2}）',
        'B3t': f'B3（MobileNet，$\\tau_{{B3}}$={tau_b3}）',
        'B4': 'B4（混合 Tier-A/B）',
    }

    en_lines = [
        '% Table III — learned IQA + hybrid (auto-generated)',
        '\\begin{table}[t]',
        '\\centering',
        '\\caption{Learned IQA and hybrid gating (ShezhenV3 test, physical resample, 3 seeds).}',
        '\\label{tab:learned-hybrid}',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        'Baseline & M1 p50 (ms) & M1 p95 (ms) & M2 valid rate & M3 retry rate \\\\',
        '\\hline',
    ]
    for bl in ['B3', 'B3t', 'B4']:
        if bl not in agg:
            continue
        a = agg[bl]
        name = label_map.get(bl, bl)
        en_lines.append(
            f'{name} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
        )
    en_lines.extend(['\\hline', '\\end{tabular}', '\\end{table}', ''])
    OUT_EN.write_text('\n'.join(en_lines), encoding='utf-8')

    zh_lines = [
        '% Table III — 学习型 IQA 与混合门控（自动生成）',
        '\\begin{table}[t]',
        '\\centering',
        '\\caption{学习型 IQA 与混合门控（ShezhenV3 测试集，物理重采，3 seeds）。}',
        '\\label{tab:learned-hybrid-zh}',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        '基线 & M1 p50 (ms) & M1 p95 (ms) & M2 有效帧率 & M3 重拍率 \\\\',
        '\\hline',
    ]
    for bl in ['B3', 'B3t', 'B4']:
        if bl not in agg:
            continue
        a = agg[bl]
        name = zh_map.get(bl, bl)
        zh_lines.append(
            f'{name} & {mean(a["p50"]):.1f} & {mean(a["p95"]):.1f} & '
            f'{mean(a["m2"]):.3f} & {mean(a["m3"]):.3f} \\\\'
        )
    zh_lines.extend(['\\hline', '\\end{tabular}', '\\end{table}', ''])
    OUT_ZH.write_text('\n'.join(zh_lines), encoding='utf-8')
    print('Wrote', OUT_EN, 'and', OUT_ZH)


if __name__ == '__main__':
    main()
