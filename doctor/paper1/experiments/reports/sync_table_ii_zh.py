#!/usr/bin/env python3
"""Sync zh/table_ii.tex from English table_ii.tex numbers."""

from __future__ import annotations

import re
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
EN = PAPER1_ROOT / 'latex/sections/table_ii.tex'
ZH = PAPER1_ROOT / 'latex/sections/zh/table_ii.tex'


def extract_latex_arg(text: str, command: str) -> str:
    marker = f'\\{command}{{'
    start = text.find(marker)
    if start < 0:
        return ''
    pos = start + len(marker)
    depth = 1
    out = []
    while pos < len(text) and depth:
        ch = text[pos]
        if ch == '{':
            depth += 1
        elif ch == '}':
            depth -= 1
            if depth == 0:
                break
        out.append(ch)
        pos += 1
    return ''.join(out)


def main() -> None:
    en_text = EN.read_text(encoding='utf-8')
    rows = re.findall(
        r'^(B[0-2]) & ([0-9.]+) & ([0-9.]+) & ([0-9.]+) & ([0-9.]+)', en_text, re.M
    )
    cap_en = extract_latex_arg(en_text, 'caption')
    cap_zh = '主实验结果（ShezhenV3-COCO 测试集，真实 Edge-IQA 分数，3 seeds）。'
    match = re.search(
        r'Main results \((?P<dataset>.+?) test split, real Edge-IQA scores, '
        r'3 seeds, (?P<n>\d+) images available; physical resample, '
        r'\$\\tau_\{B2\}\$\)\.',
        cap_en,
    )
    if match:
        dataset = match.group('dataset').replace('shezhenv3-coco', 'ShezhenV3-COCO')
        cap_zh = (
            f'主实验结果（{dataset} 测试集，真实 Edge-IQA 分数，3 个种子，'
            f'{match.group("n")} 张图像；物理重采，$\\tau_{{B2}}$）。'
        )

    lines = [
        '% Table II — auto-generated (zh sync)',
        '\\begin{table}[t]',
        '\\centering',
        f'\\caption{{{cap_zh}}}',
        '\\label{tab:main-results-zh}',
        '\\small',
        '\\resizebox{\\columnwidth}{!}{%',
        '\\begin{tabular}{lcccc}',
        '\\hline',
        '基线 & M1 p50 (ms) & M1 p95 (ms) & M2 有效帧率 & M3 重拍率 \\\\',
        '\\hline',
    ]
    for bl, p50, p95, m2, m3 in rows:
        lines.append(f'{bl} & {p50} & {p95} & {m2} & {m3} \\\\')
    lines.extend(['\\hline', '\\end{tabular}%', '}', '\\end{table}', ''])
    ZH.write_text('\n'.join(lines), encoding='utf-8')
    print('Wrote', ZH)


if __name__ == '__main__':
    main()
