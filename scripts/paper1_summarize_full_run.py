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
OUT = PAPER1 / 'docs' / '验证结果_全量.md'
OUT_LEGACY = ROOT / 'docs-zh' / 'paper1' / '论文I_全量验证结果_20260531.md'


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


def aggregate_nr() -> dict[str, dict[str, float]]:
    rows = load_json('table_ii_nr.json')
    if not isinstance(rows, list):
        return {}
    agg: dict[str, dict[str, list[float]]] = defaultdict(
        lambda: {'p50': [], 'm2': [], 'm3': []}
    )
    for row in rows:
        bl = row['baseline']
        agg[bl]['p50'].append(float(row['m1_p50_ms']))
        agg[bl]['m2'].append(float(row['m2_valid_rate']))
        agg[bl]['m3'].append(float(row['m3_retry_rate']))
    return {
        bl: {
            'm1_p50_ms': mean(a['p50']),
            'm2_valid_rate': mean(a['m2']),
            'm3_retry_rate': mean(a['m3']),
        }
        for bl, a in agg.items()
    }


def stratified_m2() -> dict[str, dict[str, float | int]]:
    out: dict[str, dict[str, float | int]] = {}
    for bl in ['B0', 'B2']:
        clear_v, blur_v = [], []
        for seed in [0, 1, 2]:
            path = RESULTS / f'main_seed{seed}_detail.csv'
            if not path.is_file():
                continue
            with path.open(encoding='utf-8') as f:
                for row in csv.DictReader(f):
                    if row['baseline'] != bl:
                        continue
                    if int(row.get('degraded', 0)):
                        blur_v.append(int(row['valid']))
                    else:
                        clear_v.append(int(row['valid']))
        if clear_v or blur_v:
            out[bl] = {
                'm2_clear': sum(clear_v) / len(clear_v) if clear_v else 0.0,
                'n_clear': len(clear_v),
                'm2_blur': sum(blur_v) / len(blur_v) if blur_v else 0.0,
                'n_blur': len(blur_v),
            }
    return out


def fmt_row(bl: str, m: dict[str, float]) -> str:
    return (
        f'| {bl} | {m["m1_p50_ms"]:.1f} | {m["m1_p95_ms"]:.1f} | '
        f'{m["m2_valid_rate"]:.3f} | {m["m3_retry_rate"]:.3f} |'
    )


def artifact_exists(rel: str) -> bool:
    full = PAPER1 / rel
    if '*' in rel:
        parent = full.parent
        return parent.is_dir() and any(parent.glob(full.name))
    return full.is_file()


def main() -> int:
    sync_ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    main_agg = aggregate_main()
    nr_agg = aggregate_nr()
    strat = stratified_m2()
    tau_b2 = load_json('recommended_tau.json')
    tau_b3 = load_json('recommended_tau_b3.json')
    cross = load_json('cross_tcm_fd.json')
    b3_meta = load_json('b3_training_meta.json')
    table_ii = load_json('table_ii.json')
    bootstrap = load_json('table_ii_bootstrap.json')

    baselines = ['B0', 'B1', 'B2', 'B3', 'B3t', 'B4']
    present = [b for b in baselines if b in main_agg]

    lines = [
        '# 论文 I · ShezhenV3 全量验证结果',
        '',
        f'> **全量完成**：2026-05-31 12:23:02（`scripts/paper1_run_tcm_finish.sh`）  ',
        f'> **同步更新**：{sync_ts}（Minor Revision 改稿 + bootstrap / 分层 M2 / NR-IQA）  ',
        f'> **日志**：`doctor/paper1/experiments/logs/tcm_full_resume.log`  ',
        f'> **快速对照**：见 [验证结果_快速.md](./验证结果_快速.md)（同目录）',
        '',
        '---',
        '',
        '## 1. 主矩阵（3 seeds × 500 帧，物理重采）',
        '',
        '来源：`experiments/results/main_seed{0,1,2}.csv`（3-seed 均值）',
        '',
        'M1 基于 **文档化仿真延迟模型**（`sim/latency_model.py`，见 `sim/NETEM.md`）。',
        '',
        '| Baseline | M1 p50 (ms) | M1 p95 (ms) | M2 valid rate | M3 retry rate |',
        '|----------|-------------|-------------|---------------|---------------|',
    ]
    for bl in present:
        lines.append(fmt_row(bl, main_agg[bl]))
    if not present:
        lines.append('| *(未完成)* | — | — | — | — |')

    lines.extend(['', '### 解读', ''])
    if 'B0' in main_agg and 'B2' in main_agg:
        b0, b2 = main_agg['B0'], main_agg['B2']
        lines.append(
            f'- **B2 vs B0**：M1 p50 {b0["m1_p50_ms"]:.1f} → **{b2["m1_p50_ms"]:.1f} ms**；'
            f'M2 {b0["m2_valid_rate"]:.3f} → **{b2["m2_valid_rate"]:.3f}**'
        )
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
            f'M1 p50={b4["m1_p50_ms"]:.1f} ms（学习型对照，RTT 高约 135 ms）'
        )
    if 'B3t' in main_agg and 'B3' in main_agg:
        lines.append(
            f'- **B3 vs B3t**：B3 M2={main_agg["B3"]["m2_valid_rate"]:.3f}，'
            f'B3t M2={main_agg["B3t"]["m2_valid_rate"]:.3f}（τ_B3 标定）'
        )

    if isinstance(bootstrap, dict) and 'B2' in bootstrap:
        b2b = bootstrap['B2']
        lines.extend([
            '',
            '### 1.1 帧级 bootstrap 95% CI（B0–B2，pooled 3×500 帧）',
            '',
            '来源：`experiments/results/table_ii_bootstrap.json`',
            '',
            '| Baseline | M2 | 95% CI |',
            '|----------|-----|--------|',
        ])
        for bl in ['B0', 'B1', 'B2']:
            if bl in bootstrap:
                b = bootstrap[bl]
                lines.append(
                    f'| {bl} | {b["m2"]:.3f} | [{b["ci_lo"]:.3f}, {b["ci_hi"]:.3f}] |'
                )

    if strat:
        lines.extend([
            '',
            '### 1.2 分层 M2（按注入 cohort，3 seeds × 500 帧合并）',
            '',
            '来源：`latex/sections/table_stratified_m2.tex`',
            '',
            '| Baseline | M2（清晰源） | M2（模糊注入） |',
            '|----------|-------------|---------------|',
        ])
        for bl in ['B0', 'B2']:
            if bl in strat:
                s = strat[bl]
                lines.append(
                    f'| {bl} | {s["m2_clear"]:.3f}（{s["n_clear"]} 帧） | '
                    f'{s["m2_blur"]:.3f}（{s["n_blur"]} 帧） |'
                )

    if nr_agg:
        lines.extend([
            '',
            '### 1.3 附录 NR-IQA（同 LangGraph 重采壳，3-seed 均值）',
            '',
            '来源：`experiments/results/table_ii_nr.json` · `replay_nr_matrix.py`',
            '',
            '| Baseline | M1 p50 (ms) | M2 | M3 |',
            '|----------|-------------|-----|-----|',
        ])
        for bl in ['Bbrisque', 'Bniqe']:
            if bl in nr_agg:
                n = nr_agg[bl]
                lines.append(
                    f'| {bl} | {n["m1_p50_ms"]:.1f} | '
                    f'{n["m2_valid_rate"]:.3f} | {n["m3_retry_rate"]:.3f} |'
                )

    lines.extend(['', '---', '', '## 2. 标定与 ROI', ''])
    if isinstance(tau_b2, dict):
        sep = tau_b2.get('separation_min_clear_max_blur', '—')
        lines.append(f'- **τ_B2**（Edge-IQA）：{tau_b2.get("tau", "—")}')
        lines.append(f'- **负分离度** `separation_min_clear_max_blur`：**{sep}**（分数重叠，Fig.3 主文展示）')
        lines.append(
            f'- **舌区 ROI**：clear med={tau_b2.get("median_clear", "—"):.4f}，'
            f'blur med={tau_b2.get("median_blur", "—"):.4f}（n={tau_b2.get("n_val", "—")}）'
        )
    if isinstance(tau_b3, dict):
        lines.append(f'- **τ_B3**（MobileNet）：{tau_b3.get("tau", tau_b3.get("tau_b3", "—"))}')
    if isinstance(cross, dict):
        lines.append(
            f'- **M5 Spearman ρ**：{cross.get("spearman", "—")}（n={cross.get("n", "—")}）'
        )

    lines.extend(['', '---', '', '## 3. B3 训练', ''])
    if isinstance(b3_meta, dict):
        acc = b3_meta.get('best_val_acc', b3_meta.get('val_acc', '—'))
        if isinstance(acc, float):
            acc = f'{acc:.4f}'
        lines.append(f'- Val accuracy：**{acc}**')
        lines.append('- 权重：`experiments/results/b3_mobilenet.pt`')

    lines.extend(['', '---', '', '## 4. 产物路径', ''])
    artifacts = [
        ('主矩阵 CSV', 'experiments/results/main_seed*.csv'),
        ('帧级 detail', 'experiments/results/main_seed*_detail.csv'),
        ('Table II JSON', 'experiments/results/table_ii.json'),
        ('bootstrap CI JSON', 'experiments/results/table_ii_bootstrap.json'),
        ('NR-IQA JSON', 'experiments/results/table_ii_nr.json'),
        ('Table II LaTeX', 'latex/sections/table_ii.tex'),
        ('Table III LaTeX', 'latex/sections/table_iii.tex'),
        ('分层 M2 LaTeX', 'latex/sections/table_stratified_m2.tex'),
        ('NR-IQA LaTeX', 'latex/sections/table_nr_iqa.tex'),
        ('Fig.3 标定直方图', 'figures/fig_iqa_hist.pdf'),
        ('Fig.4 RTT CDF', 'figures/fig5_rtt_cdf.pdf'),
        ('Fig.5 M2 柱图', 'figures/fig6_valid_rate.pdf'),
        ('Fig.6 Pareto', 'figures/fig7_pareto_m2_m1.pdf'),
        ('Fig.7 τ 消融', 'figures/fig7_ablation_tau.pdf'),
        ('PDF（英文）', 'latex/main.pdf'),
        ('PDF（中文）', 'latex/main-zh.pdf'),
    ]
    for name, path in artifacts:
        mark = '✅' if artifact_exists(path) else '⏳'
        lines.append(f'- {mark} **{name}**：`doctor/paper1/{path}`')

    if isinstance(table_ii, list):
        lines.append(f'- Table II JSON 行数：**{len(table_ii)}**（6 baselines × 3 seeds）')

    lines.extend([
        '',
        '---',
        '',
        '## 5. 投稿与审核状态（2026-06-04）',
        '',
        '| 项 | 状态 |',
        '|----|------|',
        '| 多智能体审核 | Minor Revision **7.2/10**（`reviews/20260603-213904/`） |',
        '| P0–P2 改稿 | ✅ 12/12 完成 |',
        '| 学习手册 | `doctor/paper1/docs/study/README.md` |',
        '',
        '---',
        '',
        '*由 `scripts/paper1_summarize_full_run.py` 自动生成；改稿产物见 `experiments/reports/build_paper1_artifacts.py`*',
        '',
    ])
    body = '\n'.join(lines)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(body, encoding='utf-8')
    print(f'Wrote {OUT}')
    # docs-zh 保留跳转 stub，避免双处维护数字
    stub = '\n'.join([
        '# 论文 I · ShezhenV3 全量验证结果',
        '',
        '> **已迁移**：数字唯一出口为 [`doctor/paper1/docs/验证结果_全量.md`](../../doctor/paper1/docs/验证结果_全量.md)。',
        '> 请在该文件或 `experiments/results/table_ii.json` 查阅；勿编辑本页。',
        '',
        f'同步时间：{sync_ts}',
        '',
    ])
    OUT_LEGACY.parent.mkdir(parents=True, exist_ok=True)
    OUT_LEGACY.write_text(stub, encoding='utf-8')
    print(f'Wrote stub {OUT_LEGACY}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
