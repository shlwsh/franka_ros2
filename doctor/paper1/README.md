# Paper I — Edge-IQA + LangGraph

论文 I 算法与实验代码，与 `franka_ros2` **同仓库**管理。

> **更新**：2026-06-04 · 全量主矩阵（3 seeds × 500 帧）+ Minor Revision 改稿（P0–P2 已完成）  
> **审核**：`reviews/20260603-213904/`（PI **7.2/10**，Minor Revision）  
> **学习手册**：`docs/study/README.md`

---

## 路径

| 变量 | 默认值 |
|------|--------|
| `PAPER1_ROOT` | `<repo_root>/doctor/paper1` |
| `FRANKA_ROS2_ROOT` | 本仓库根目录 |

```bash
export PAPER1_ROOT="/root/work/paper1/doctor/paper1"
# 或省略（franka_api_server 自动解析仓库内路径）
```

---

## 目录

| 路径 | 说明 |
|------|------|
| `docs/` | **实验数字 L1 汇总**（唯一 Markdown 出口） |
| `edge_iqa/` | 边侧 IQA（Laplacian+曝光；B3 MobileNet） |
| `langgraph_router/` | 置信度路由 + B2d/m/u 扩展 |
| `sim/` | 延迟模型、`resample_physics.yaml` |
| `experiments/` | 主矩阵、标定、报告脚本 |
| `figures/` | 论文图（Fig.3–8、Pareto、M6） |
| `data/papers/` | 延伸阅读 PDF；**RA-L 正文引用对照见 [`data/papers/README.md`](data/papers/README.md)** |
| `latex/` | 中英文稿 `main.tex` / `main-zh.pdf` |
| `reviews/` | 多智能体审核报告 |
| `submission/RA-L_20260529/` | 投稿包（Cover Letter、GA） |
| `supplementary/` | 在线 Walkthrough（移出正文） |
| `patent/` | 专利交底提纲（可选） |

---

## 与 franka_api_server 的关系

- **算法不进 ROS**：`edge_iqa`、`langgraph_router` 仅在本目录。
- **执行在** `franka_api_server`：vision / skills / motion HTTP。
- 设置 `PAPER1_MODE=1` 禁用阻抗类 API。

---

## 当前主结果（ShezhenV3，定稿数字）

| 项 | 值 |
|----|-----|
| τ_B2 | **0.465**（ROI val；`recommended_tau.json`） |
| 负分离度 | **−0.541**（`separation_min_clear_max_blur`） |
| B2 vs B0 M1 p50 | 374 → **208 ms**（仿真 RTT 模型） |
| B2 vs B0 M2 | 0.560 → **0.604**（bootstrap CI [0.579, 0.628]） |
| B4 Hybrid M2 | **0.936**（Table III） |
| Edge-IQA p95 | **9.57 ms** @512px CPU |

主表 M1 来自 `sim/latency_model.py` 文档化模型；M6 Franka 辅轨**不进** Table II。

---

## Edge-IQA（阶段 2）

```bash
cd "$PAPER1_ROOT"
pip install -r requirements-paper1.txt
python3 scripts/synth_degrade.py         # 合成 val 集（无 TCM 时）
python3 -m pytest edge_iqa/tests -q
python3 experiments/edge_iqa/calibrate_tau_tcm.py   # ShezhenV3 → recommended_tau.json
python3 figures/plot_iqa_hist.py
```

---

## 闭环路由（阶段 3）

```bash
cd "$FRANKA_ROS2_ROOT"
bash scripts/paper1_closed_loop.sh
python3 scripts/validate_jsonl.py doctor/paper1/experiments/logs/run_001.jsonl
```

---

## 主实验与文稿（阶段 4–5）

```bash
# 一键全量（推荐）
bash scripts/paper1_run_tcm_full.sh

# 或断点续跑
bash scripts/paper1_run_tcm_finish.sh

# 改稿产物：bootstrap / 分层 M2 / Pareto
python3 experiments/reports/build_paper1_artifacts.py
python3 experiments/reports/build_table_ii.py   # 写入 bootstrap 表注

# NR-IQA 附录（BRISQUE/NIQE）
python3 experiments/replay_nr_matrix.py
python3 experiments/reports/build_table_nr_iqa.py

# 辅轨 + PDF
bash scripts/paper1_run_m6.sh
bash scripts/paper1_build_draft.sh
```

复现说明：`REPRODUCE.md`；Franka 栈见 `docs-zh/paper1/V19/REPRODUCE_franka.md`。

---

## 快速检查

```bash
bash scripts/check_paper1_env.sh
bash scripts/verify_paper1_phases.sh
```

---

## 关联文档

| 文档 | 路径 |
|------|------|
| 离线复现 | `REPRODUCE.md` |
| 延迟模型 | `sim/NETEM.md` |
| 投稿包 | `submission/RA-L_20260529/` |
| 在线 Walkthrough | `supplementary/online_walkthrough.md` |
| 文档与数据索引 | [`docs/README.md`](docs/README.md) |
| 全量验证汇总 | [`docs/验证结果_全量.md`](docs/验证结果_全量.md) |
| 快速验证对照 | [`docs/验证结果_快速.md`](docs/验证结果_快速.md) |
| 学习手册（叙事） | [`docs/study/`](docs/study/README.md) |
