# M6 vs M1 趋势备忘录（辅轨）

> **更新**：2026-06-04  
> **勿将本文件数字写入 Table II。** 主实验 M1–M3 仅来自 `main_seed*.csv`（仿真 RTT 模型）。

## 观测

| 轨道 | 指标 | 值 (ms) | 说明 |
|------|------|---------|------|
| 主轨 B2 (M1 p50, 3 seeds 均值) | 离线仿真 | **208.3** | 含云上传 + 物理重采 |
| 主轨 B0 (M1 p50) | 离线仿真 | **374.0** | naive 全上传 |
| 辅轨 M6 (50 trial p50) | franka 闭环 JSONL | **7.38** | 仅本地 IQA+路由 |

> 历史草稿曾误写 B2 p50=364 ms，已作废；定稿以 `table_ii.json` 为准。

## 结论（叙述用）

- M6 仅含 **本地 IQA+路由+日志** 延迟（无云上传仿真），数值低于主轨 M1 属预期；**勿与 Table II 混比绝对值**。  
- M6 **不替代**主轨统计检验；投稿时 M6 仅作 Supplementary Fig.S1（执行栈可复现、路由决策分布）。  
- **趋势一致**：主轨 B2 的 M1 p50 低于 B0、M2 由 0.560 升至 0.604；辅轨 50 trial 中清晰帧 → `upload_cloud`、模糊帧 → `resample_edge`。

## 分层 M2（主轨补充，非 M6）

| Cohort | B0 M2 | B2 M2 |
|--------|-------|-------|
| clear-source | 0.733 | 0.737 |
| blur-injected | 0.373 | **0.460** |

来源：`table_stratified_m2.tex`（3 seeds × 500 帧合并）

## 数据文件

- 主轨：`experiments/results/main_seed{0,1,2}.csv`、`table_ii.json`  
- 辅轨：`experiments/results/franka_m6_rtt.csv`、`franka_m6_summary.json`

## 复现

```bash
bash scripts/paper1_run_m6.sh
python3 figures/plot_m6_rtt.py   # -> fig_s1_franka_rtt.pdf
```
