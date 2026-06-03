# 论文 I 学习手册

> **目标读者**：刚接触本课题的学生，需快速掌握论文核心内容以应对导师审阅与答辩拷问。  
> **数字唯一出口**：L1 [`../README.md`](../README.md) · L0 `../../experiments/results/*.json`（仓库路径亦写作 `doctor/paper1/docs/`、`doctor/paper1/experiments/results/`）  
> **维护技能**：Cursor `@paper1-study-handbook`（`.cursor/skills/paper1-study-handbook/`）  
> **Shell 命令**：以下 `scripts/`、`bash` 均在**仓库根目录**执行。  
> **更新日期**：2026-06-04

---

## 如何使用

| 阶段 | 推荐阅读顺序 | 预计时间 |
|------|-------------|----------|
| **第 1 天：建立全局观** | [01_论文全景与定位.md](./01_论文全景与定位.md) → [02_核心概念与技术原理.md](./02_核心概念与技术原理.md) 前半 | 2–3 小时 |
| **算法扩展** | [08_算法扩展详解.md](./08_算法扩展详解.md) → `bash scripts/paper1_run_algo_quick.sh` | 45 分钟 |
| **第 2 天：吃透方法与数据** | [02](./02_核心概念与技术原理.md) 后半 → [03_实验数据与图表解读.md](./03_实验数据与图表解读.md) → [06_Edge-IQA算法详解与业界对比.md](./06_Edge-IQA算法详解与业界对比.md) | 3–4 小时 |
| **第 3 天：实战与拷问** | [04_系统架构与代码地图.md](./04_系统架构与代码地图.md) → [05_导师拷问速答.md](./05_导师拷问速答.md) | 2–3 小时 |
| **临阵前 30 分钟** | [05_导师拷问速答.md](./05_导师拷问速答.md)「必背数字」+ [03](./03_实验数据与图表解读.md) §1 + [验证结果_全量](../验证结果_全量.md) | 30 分钟 |
| **投稿前速览** | [审核行动清单](../../reviews/20260603-213904/行动清单.md)（P0–P2 已全部完成） | 15 分钟 |

---

## 文档目录

| 文件 | 内容 |
|------|------|
| [01_论文全景与定位.md](./01_论文全景与定位.md) | 论文标题、科学问题、三条贡献、投稿就绪度 |
| [02_核心概念与技术原理.md](./02_核心概念与技术原理.md) | Edge-IQA、LangGraph、B0–B4、M1–M6、负分离度 |
| [03_实验数据与图表解读.md](./03_实验数据与图表解读.md) | 图表叙事（数字回链 `doctor/paper1/docs/`） |
| [04_系统架构与代码地图.md](./04_系统架构与代码地图.md) | 双仓、API、JSONL、验收命令 |
| [05_导师拷问速答.md](./05_导师拷问速答.md) | 50+ 问答、必背数字、陷阱 |
| [06_Edge-IQA算法详解与业界对比.md](./06_Edge-IQA算法详解与业界对比.md) | 实现、业界对比、§6 负分离度答辩 |
| [07_LangGraph与FSM对比深度分析.md](./07_LangGraph与FSM对比深度分析.md) | LangGraph vs FSM 基准 |
| [08_算法扩展详解.md](./08_算法扩展详解.md) | B2d/m/u、物理重采、Hybrid B4 |

---

## 必背一句话（电梯演讲）

> ShezhenV3-COCO 舌区 ROI **τ_B2=0.465**（`separation_min_clear_max_blur=−0.541`）；全量 **B2** M1 p50 **208 ms**、M2 **0.604**；**B4** M2 **0.936** 但 RTT 高约 135 ms。主表 M1 为仿真延迟模型，M6 仅验证趋势。  
> 数字出处：[验证结果_全量.md](../验证结果_全量.md)

---

## 当前投稿状态（2026-06-04）

| 项 | 状态 |
|----|------|
| 多智能体审核 | **Minor Revision** 7.2/10 · `doctor/paper1/reviews/20260603-213904/` |
| P0–P2 改稿 | ✅ 全部完成 |
| 中英文 PDF | `doctor/paper1/latex/main.pdf` / `main-zh.pdf` |

---

## 关联资源（均在 `doctor/paper1` 或仓库脚本）

| 资源 | 路径 |
|------|------|
| **文档与数据索引** | [`doctor/paper1/docs/README.md`](../README.md) |
| 全量验证汇总 | [`doctor/paper1/docs/验证结果_全量.md`](../验证结果_全量.md) |
| 快速验证对照 | [`doctor/paper1/docs/验证结果_快速.md`](../验证结果_快速.md) |
| 离线复现 | [`doctor/paper1/REPRODUCE.md`](../../REPRODUCE.md) |
| 仿真 RTT 模型 | [`doctor/paper1/sim/NETEM.md`](../../sim/NETEM.md) |
| M6 辅轨说明 | [`doctor/paper1/experiments/reports/m6_vs_m1_trend.md`](../../experiments/reports/m6_vs_m1_trend.md) |
| 审核报告 | `doctor/paper1/reviews/20260603-213904/` |
| 刷新全量 Markdown | `python3 scripts/paper1_summarize_full_run.py` |
