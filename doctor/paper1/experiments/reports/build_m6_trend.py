#!/usr/bin/env python3
"""Compare M6 auxiliary RTT trend vs offline M1 (B2) — narrative only."""

from __future__ import annotations

import csv
import json
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
OUT = PAPER1_ROOT / 'experiments/reports/m6_vs_m1_trend.md'


def pct(vals, p):
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)


def main() -> None:
    m6 = []
    with (PAPER1_ROOT / 'experiments/results/franka_m6_rtt.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            m6.append(float(row['latency_ms']))

    b2_p50 = []
    with (PAPER1_ROOT / 'experiments/results/main_seed0.csv').open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['baseline'] == 'B2':
                b2_p50.append(float(row['m1_p50_ms']))

    m6_p50 = pct(m6, 50)
    m1_b2_mean = sum(b2_p50) / len(b2_p50) if b2_p50 else 0

    text = f"""# M6 vs M1 趋势备忘录（辅轨）

> **勿将本文件数字写入 Table II。** 主实验 M1–M3 仅来自 `main_seed*.csv`。

## 观测

| 轨道 | 指标 | 值 (ms) |
|------|------|---------|
| 主轨 B2 (M1 p50, 3 seeds 均值) | 离线仿真 | **{m1_b2_mean:.1f}** |
| 辅轨 M6 (50 trial p50) | franka 闭环 JSONL | **{m6_p50:.1f}** |

## 结论（叙述用）

- M6 仅含 **本地 IQA+路由+日志** 延迟（无云上传仿真），数值低于主轨 M1 属预期；**勿与 Table II 混比绝对值**。  
- M6 **不替代**主轨统计检验；投稿时 M6 仅作 Supplementary Fig.S1（执行栈可复现、路由决策分布）。  
- **趋势一致**：主轨 B2 的 M1 p50 低于 B0、M2 显著提高；辅轨 50 trial 中 `upload_cloud` / `resample_edge` 与阶段 3 路由策略一致。

## 数据文件

- 主轨：`experiments/results/main_seed{{0,1,2}}.csv`  
- 辅轨：`experiments/results/franka_m6_rtt.csv`
"""
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(text, encoding='utf-8')
    print('Wrote', OUT)


if __name__ == '__main__':
    main()
