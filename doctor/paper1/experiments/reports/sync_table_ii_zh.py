#!/usr/bin/env python3
"""Sync zh/table_ii.tex from English table_ii.tex numbers."""

from __future__ import annotations

import re
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
EN = PAPER1_ROOT / 'latex/sections/table_ii.tex'
ZH = PAPER1_ROOT / 'latex/sections/zh/table_ii.tex'


def main() -> None:
    en_text = EN.read_text(encoding='utf-8')
    rows = re.findall(
        r'^(B[0-3]) & ([0-9.]+) & ([0-9.]+) & ([0-9.]+) & ([0-9.]+)', en_text, re.M
    )
    cap_match = re.search(r'\\caption\{([^}]+)\}', en_text)
    cap_en = cap_match.group(1) if cap_match else ''
    cap_zh = cap_en.replace(
        'Main results (shezhenv3-coco test split, real Edge-IQA scores, 3 seeds, 553 images available).',
        '主实验结果（ShezhenV3-COCO 测试集，真实 Edge-IQA 分数，3 个种子，553 张图像）。',
    )
    if cap_zh == cap_en:
        cap_zh = '主实验结果（ShezhenV3-COCO 测试集，真实 Edge-IQA 分数，3 seeds）。'

    lines = [
        '% Table II — auto-generated (zh sync)',
        '\\begin{table}[t]',
        '\\centering',
        f'\\caption{{{cap_zh}}}',
        '\\label{tab:main-results-zh}',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        '基线 & M1 p50 (ms) & M1 p95 (ms) & M2 有效帧率 & M3 重拍率 \\\\',
        '\\hline',
    ]
    for bl, p50, p95, m2, m3 in rows:
        lines.append(f'{bl} & {p50} & {p95} & {m2} & {m3} \\\\')
    lines.extend(['\\hline', '\\end{tabular}', '\\end{table}', ''])
    ZH.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote', ZH)


if __name__ == '__main__':
    main()
