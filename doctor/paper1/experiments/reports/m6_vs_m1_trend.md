# M6 vs M1 趋势备忘录（辅轨）

> **勿将本文件数字写入 Table II。** 主实验 M1–M3 仅来自 `main_seed*.csv`。

## 观测

| 轨道 | 指标 | 值 (ms) |
|------|------|---------|
| 主轨 B2 (M1 p50, 3 seeds 均值) | 离线仿真 | **364.3** |
| 辅轨 M6 (50 trial p50) | franka 闭环 JSONL | **7.4** |

## 结论（叙述用）

- M6 仅含 **本地 IQA+路由+日志** 延迟（无云上传仿真），数值低于主轨 M1 属预期；**勿与 Table II 混比绝对值**。  
- M6 **不替代**主轨统计检验；投稿时 M6 仅作 Supplementary Fig.S1（执行栈可复现、路由决策分布）。  
- **趋势一致**：主轨 B2 的 M1 p50 低于 B0、M2 显著提高；辅轨 50 trial 中 `upload_cloud` / `resample_edge` 与阶段 3 路由策略一致。

## 数据文件

- 主轨：`experiments/results/main_seed{0,1,2}.csv`  
- 辅轨：`experiments/results/franka_m6_rtt.csv`
