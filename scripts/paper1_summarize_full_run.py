#!/usr/bin/env python3
"""Summarize Paper I full TCM pipeline results into docs-zh markdown."""

from __future__ import annotations

import csv
import json
import statistics
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PAPER1 = ROOT / 'doctor' / 'paper1'
RESULTS = PAPER1 / 'experiments' / 'results'
OUT = ROOT / 'docs-zh' / 'paper1' / '论文I_全量验证结果_20260531.md'


def load_json(name: str) -> dict | list | None:
    path = RESULTS / name
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding='utf-8'))


def mean(xs: list[float]) -> float:
    return statistics.mean(xs) if xs else float('nan')


def aggregate_main() -> dict[str, dict[str, float]]:
    agg: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {'p50': [], 'p95': [], 'm2': [], 'm3': []}
    )
    for seed in [0, 1, 2]:
        path = RESULTS / f'main_seed{seed}.csv'
        if not path.is_file():
            continue
        with path.open(encoding='utf-8') as f:
            for row in csv.DictReader(f):
                bl = row['baseline']
                agg[bl]['p50'].append(float(row['m1_p50_ms']))
                agg[bl]['p95'].append(float(row['m1_p95_ms']))
                agg[bl]['m2'].append(float(row['m2_valid_rate']))
                agg[bl]['m3'].append(float(row['m3_retry_rate']))
    out: dict[str, dict[str, float]] = {}
    for bl, a in agg.items():
        out[bl] = {
            'm1_p50_ms': mean(a['p50']),
            'm1_p95_ms': mean(a['p95']),
            'm2_valid_rate': mean(a['m2']),
            'm3_retry_rate': mean(a['m3']),
            'n_seeds': len(a['p50']),
        }
    return out


def fmt_row(bl: str, m: dict[str, float]) -> str:
    return (
        f'| {bl} | {m["m1_p50_ms"]:.1f} | {m["m1_p95_ms"]:.1f} | '
        f'{m["m2_valid_rate"]:.3f} | {m["m3_retry_rate"]:.3f} |'
    )


def main() -> int:
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    main_agg = aggregate_main()
    tau_b2 = load_json('recommended_tau.json')
    tau_b3 = load_json('recommended_tau_b3.json')
    roi = load_json('roi_ablation.json')
    cross = load_json('cross_tcm_fd.json')
    b3_meta = load_json('b3_training_meta.json')
    table_ii = load_json('table_ii.json')

    baselines = ['B0', 'B1', 'B2', 'B3', 'B3t', 'B4']
    present = [b for b in baselines if b in main_agg]

    lines = [
        '# 论文 I · ShezhenV3 全量验证结果',
        '',
        f'> **生成时间**：{ts}  ',
        f'> **脚本**：`scripts/paper1_run_tcm_full_resume_step6.sh`  ',
        f'> **日志**：`doctor/paper1/experiments/logs/tcm_full_resume.log`',
        '',
        '---',
        '',
        '## 1. 主矩阵（3 seeds × 500 帧，物理重采）',
        '',
        '来源：`experiments/results/main_seed{0,1,2}.csv`（3-seed 均值）',
        '',
        '| Baseline | M1 p50 (ms) | M1 p95 (ms) | M2 valid rate | M3 retry rate |',
        '|----------|-------------|-------------|---------------|---------------|',
    ]
    for bl in present:
        lines.append(fmt_row(bl, main_agg[bl]))
    if not present:
        lines.append('| *(未完成)* | — | — | — | — |')

    lines.extend(['', '### 解读', ''])
    if 'B2' in main_agg:
        b2 = main_agg['B2']
        lines.append(
            f'- **B2（论文主 claim）**：M2={b2["m2_valid_rate"]:.3f}，'
            f'M1 p50={b2["m1_p50_ms"]:.1f} ms，M3={b2["m3_retry_rate"]:.3f}'
        )
    if 'B4' in main_agg:
        b4 = main_agg['B4']
        lines.append(
            f'- **B4 Hybrid**：M2={b4["m2_valid_rate"]:.3f}，'
            f'M1 p50={b4["m1_p50_ms"]:.1f} ms'
        )
    if 'B3t' in main_agg and 'B3' in main_agg:
        lines.append(
            f'- **B3 vs B3t**：B3 M2={main_agg["B3"]["m2_valid_rate"]:.3f}，'
            f'B3t M2={main_agg["B3t"]["m2_valid_rate"]:.3f}（τ_B3 标定）'
        )

    lines.extend(['', '---', '', '## 2. 标定与 ROI', ''])
    if isinstance(tau_b2, dict):
        lines.append(
            f'- **τ_B2**（Edge-IQA）：{tau_b2.get("tau", tau_b2.get("recommended_tau", "—"))}'
        )
    if isinstance(tau_b3, dict):
        lines.append(f'- **τ_B3**（MobileNet）：{tau_b3.get("tau", tau_b3.get("tau_b3", "—"))}')
    if isinstance(cross, dict):
        lines.append(
            f'- **M5 Spearman ρ**：{cross.get("spearman", "—")}（n={cross.get("n", "—")}）'
        )
    if isinstance(roi, dict):
        roi_part = roi.get('tongue_roi', roi)
        lines.append(
            f'- **舌区 ROI**：τ={roi_part.get("tau", "—")}，'
            f'clear med={roi_part.get("median_clear", "—")}，'
            f'blur med={roi_part.get("median_blur", "—")}'
        )

    lines.extend(['', '---', '', '## 3. B3 训练', ''])
    if isinstance(b3_meta, dict):
        lines.append(f'- Val accuracy：**{b3_meta.get("best_val_acc", b3_meta.get("val_acc", "—"))}**')
        lines.append(f'- 权重：`experiments/results/b3_mobilenet.pt`')

    lines.extend(['', '---', '', '## 4. 产物路径', ''])
    artifacts = [
        ('主矩阵 CSV', 'experiments/results/main_seed*.csv'),
        ('Table II JSON', 'experiments/results/table_ii.json'),
        ('Table II LaTeX', 'latex/sections/table_ii.tex'),
        ('Table III LaTeX', 'latex/sections/table_iii.tex'),
        ('主图', 'figures/main_*.png'),
        ('PDF', 'latex/main.pdf'),
    ]
    for name, path in artifacts:
        full = PAPER1 / path.replace('*', '')
        if '*' in path:
            parent = PAPER1 / path.rsplit('/', 1)[0]
            exists = parent.is_dir() and any(parent.glob(path.split('/')[-1]))
        else:
            exists = full.is_file()
        mark = '✅' if exists else '⏳'
        lines.append(f'- {mark} **{name}**：`doctor/paper1/{path}`')

    if isinstance(table_ii, list):
        lines.extend(['', f'- Table II JSON 行数：{len(table_ii)}'])

    lines.extend(['', '---', '', '*由 `scripts/paper1_summarize_full_run.py` 自动生成*', ''])
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text('\n'.join(lines), encoding='utf-8')
    print(f'Wrote {OUT}')
    print('\n'.join(lines[8:20]))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
