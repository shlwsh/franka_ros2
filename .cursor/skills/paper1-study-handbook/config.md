# Paper I 学习手册 — 本仓库配置

| 变量 | 值 | 说明 |
|------|-----|------|
| **PAPER1_ROOT** | `doctor/paper1` | 算法、实验、LaTeX、数据文档 |
| **STUDY_ROOT** | `doctor/paper1/docs/study` | 学习手册（L2 叙事层，中文） |
| **DOCS_L1** | `{PAPER1_ROOT}/docs` | 实验数字人类可读汇总（L1） |
| **RESULTS_L0** | `{PAPER1_ROOT}/experiments/results` | JSON/CSV 唯一机器源（L0） |
| **REVIEWS** | `{PAPER1_ROOT}/reviews` | 多智能体审核报告（可选输入） |

## 解析规则

1. 工作区根 = 含 `colcon`/`franka_api_server` 的仓库根。  
2. 路径 = `工作区根` + 上表相对路径。  
3. 用户指定其他论文目录时，覆盖 `PAPER1_ROOT`；`STUDY_ROOT` 默认为 `{PAPER1_ROOT}/docs/study`。

## 相对链接（从 `STUDY_ROOT` 到 L1 / PAPER1_ROOT）

| 目标 | 相对路径 |
|------|----------|
| docs 索引 | `../README.md` |
| 全量汇总 | `../验证结果_全量.md` |
| 快速汇总 | `../验证结果_快速.md` |
| REPRODUCE | `../../REPRODUCE.md` |
| NETEM | `../../sim/NETEM.md` |
| 审核报告 | `../../reviews/{run_id}/` |

## 旧路径

`docs-zh/paper1/study/` 仅保留跳转 stub；**勿**在新内容中链接或写入该目录。
