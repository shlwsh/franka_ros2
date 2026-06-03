# Paper I · 文档与数据出口（唯一权威）

> **原则**：凡涉及实验数字、标定、图表路径，**以本目录及 `../experiments/results/` 为准**。  
> **学习手册**（`docs-zh/paper1/study/`）仅作叙事解读，**不另维护数字副本**；发现不一致时以 JSON/CSV 为准并运行汇总脚本刷新 Markdown。

---

## 数据层级

| 层级 | 路径 | 用途 |
|------|------|------|
| **L0 机器可读** | `experiments/results/*.json`、`main_seed*.csv` | 脚本、LaTeX、论文 Table II 唯一数据源 |
| **L1 人类可读汇总** | 本目录 `验证结果_*.md` | 导师/学生速查；由脚本从 L0 生成 |
| **L2 叙事解读** | `docs-zh/paper1/study/` | 概念、答辩、架构；引用 L0/L1，不引用 `docs-zh/paper1/论文I_*` |

---

## 文档索引

| 文档 | 说明 | 刷新方式 |
|------|------|----------|
| [验证结果_全量.md](./验证结果_全量.md) | 3 seeds × 500 帧主矩阵、bootstrap、分层 M2、NR-IQA | `python3 scripts/paper1_summarize_full_run.py` |
| [验证结果_快速.md](./验证结果_快速.md) | 1 seed × 80 帧冒烟对照 | 手更或读 `quick_summary.json` |
| [../REPRODUCE.md](../REPRODUCE.md) | 离线复现步骤 | — |
| [../sim/NETEM.md](../sim/NETEM.md) | 仿真 RTT 延迟模型 | — |
| [../experiments/reports/m6_vs_m1_trend.md](../experiments/reports/m6_vs_m1_trend.md) | M6 辅轨 vs 主轨（勿混比） | — |
| [../supplementary/online_walkthrough.md](../supplementary/online_walkthrough.md) | 在线 Walkthrough | — |
| [../reviews/20260603-213904/执行摘要.md](../reviews/20260603-213904/执行摘要.md) | 多智能体审核 | — |
| [../submission/RA-L_20260529/](../submission/RA-L_20260529/) | 投稿包 | — |

---

## 核心 JSON 速查

| 文件 | 内容 |
|------|------|
| `experiments/results/table_ii.json` | 主矩阵 18 行（6 baselines × 3 seeds） |
| `experiments/results/table_ii_bootstrap.json` | B0–B2 帧级 M2 CI |
| `experiments/results/recommended_tau.json` | τ_B2、separation、ROI 中位数 |
| `experiments/results/recommended_tau_b3.json` | τ_B3 |
| `experiments/results/quick_summary.json` | 快速验证 |
| `experiments/results/algo_quick_summary.json` | B2d/m/u 消融 |
| `experiments/results/table_ii_nr.json` | NR-IQA 附录 |
| `experiments/results/cross_tcm_fd.json` | M5 Spearman |
| `experiments/results/network_sweep_quick.json` | 网络扰动 quick |

---

## 一键刷新 L1 文档

```bash
# 仓库根目录
python3 scripts/paper1_summarize_full_run.py
```

---

## 学习手册入口

概念与答辩：`docs-zh/paper1/study/README.md`（阅读顺序与必背话术；数字回链本目录）。
