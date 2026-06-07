# 本仓库配置（franka_ros2 / paper1）

复制技能到其他项目时，请改写本文件或新建 `config.local.md`（见 [README.md](README.md)）。

## 项目标识

| 项 | 值 |
|----|-----|
| 项目名 | franka_ros2 / doctor/paper1 |
| 论文主题 | Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging |
| 目标期刊（主） | IEEE Robotics and Automation Letters（RA-L） |
| 目标期刊（备） | Robotics and Computer-Integrated Manufacturing（RCIM）或作者指定期刊 |
| 主审语言 | 英文主稿，中文稿用于术语与数值同步抽查 |

## 期刊模式

| 变量 | 值 | 说明 |
|------|-----|------|
| **TARGET_JOURNAL** | `RAL`（默认）或 `RCIM` | 审核时追加对应投稿前检查 |
| 投稿要点 | [期刊投稿要点.md](期刊投稿要点.md) | 以官网最新 author instructions 为最终准则 |

## 路径（相对仓库根）

| 变量 | 值 | 说明 |
|------|-----|------|
| **PAPER1_ROOT** | `doctor/paper1` | 相对**工作区根目录**的论文与实验路径 |
| **主稿英文** | `{PAPER1_ROOT}/latex/main.tex` | 盲审主语言默认英文 |
| **RA-L 主稿** | `{PAPER1_ROOT}/latex/main-ral.tex` | 投稿/压缩版主稿 |
| **主稿中文** | `{PAPER1_ROOT}/latex/main-zh.tex` | 预检可选中英数字对照 |
| **英文分节** | `{PAPER1_ROOT}/latex/sections/*.tex` | 主体章节 |
| **中文分节** | `{PAPER1_ROOT}/latex/sections/zh/*.tex` | 同步抽查 |
| **实验数据** | `{PAPER1_ROOT}/experiments/results/*.json` | L0 数值真相 |
| **引用归档** | `{PAPER1_ROOT}/data/papers/` | PDF、索引、引用审计 |
| **参考文献** | `{PAPER1_ROOT}/latex/references.bib` | bib 入口 |
| **审计脚本** | `{PAPER1_ROOT}/scripts/check_paper1_refs.py`、`paper1_audit_papers.py` | 引用、交叉引用检查 |
| **学习手册** | `{PAPER1_ROOT}/docs/study/` | 领域与投稿策略参考 |
| **评审输出** | `{PAPER1_ROOT}/reviews/{run_id}/` | `run_id` = `YYYYMMDD-HHmmss` |

## 解析规则（执行 Agent）

1. 工作区根 = 含 `.cursor/skills/` 或 `colcon`/`package.xml` 的仓库根（用户打开的根目录）。
2. 所有路径 = `工作区根` + 上表相对路径。
3. 若用户消息中指定了论文目录（如「论文在 `thesis/ch1`」），则以用户为准覆盖 `PAPER1_ROOT`。
4. 若用户指定目标期刊，则覆盖 `TARGET_JOURNAL`；否则按 RA-L 口径审稿，RCIM 只作为备选风格风险提示。

## 文档入口

| 文件 | 用途 |
|------|------|
| [审核细则.md](审核细则.md) | Phase 1–2 勾选清单，执行时优先读 |
| [期刊投稿要点.md](期刊投稿要点.md) | RA-L / RCIM 投稿前检查 |
| [参考文献归档细则.md](参考文献归档细则.md) | `data/papers/` 与引用核实 |
| [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) | 重大修改、二次评审、版本化 PDF |
