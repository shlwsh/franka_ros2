# 论文 I · AI 主导科研执行总纲（压缩版 V19）

> **版本**：AI-master-1 | 2026-05-29  
> **执行主体**：Cursor Agent（主研发）+ 学生（环境确认、真机/大图可选、投稿签字）  
> **单仓库**：边–端在 `franka_api_server` 等包；算法与主实验在 **`doctor/paper1/`**（默认 `$FRANKA_ROS2_ROOT/doctor/paper1`）  
> **投稿目标**：2026-09-30（保留 2 周缓冲；AI 排期按 **8 个自然周** 完成核心科研产出）

---

## 1. 压缩原则

| 原规划 | 压缩后 |
|--------|--------|
| 学生主研 + 多 Sprint 人工分工 | **AI 串并行实现**；学生仅 **P0 检查点**（挂载、testall、可选 RViz 微调） |
| F0–F4 与 P0–P6 分 19 周 | **5 个科研阶段**，每阶段绑定 **论文章节 + 图表 + 指标** |
| 先等数据集全量再写 scorer | **最小可发表路径**：公开舌象子集 / 合成退化图先跑通 M1–M3；TCM 全量并行不阻塞 |
| 两仓周会 | **阶段末一次性验收** + JSONL/CSV 工件入库 |

**不变量**（与 [franka_ros2_优化改进计划.md](./franka_ros2_优化改进计划.md) 一致）：算法不进 ROS；`PAPER1_MODE` 禁用阻抗 API；主实验数字仅来自离线 `run_matrix`；franka 辅轨 M6 只论证趋势。

---

## 2. 五阶段总览（科研成果对齐）

| 阶段 | 日历（建议） | 科研问题 | 论文产出 | 工程收口 |
|------|--------------|----------|----------|----------|
| **[阶段 1](./phases/阶段1_系统基座与架构证据.md)** | W1（06.01–06.07） | 云–边–端架构能否可演示？ | **§3**、**Fig.1** 定稿素材 | F0 + F1 骨架 + paper1 目录 |
| **[阶段 2](./phases/阶段2_Edge-IQA与阈值标定.md)** | W2–W3（06.08–06.21） | 边侧 IQA 是否可信且够快？ | **§4.1**、**Fig.3**、τ、**M5** 初稿 | F2 + P2-* |
| **[阶段 3](./phases/阶段3_闭环路由与可复现日志.md)** | W4–W5（06.22–07.05） | 路由闭环是否可测试、可日志复现？ | **§4.2–4.3**、**Fig.2**、JSONL 样例 | F3（10 trial）+ P3-* |
| **[阶段 4](./phases/阶段4_主实验与辅轨M6.md)** | W6–W8（07.06–07.26） | B0–B3 是否支撑 M1–M3 结论？辅轨趋势？ | **§5.1–5.2**、**Fig.5–6**、**Table II**、**Fig.S1** | P4-* + M6 |
| **[阶段 5](./phases/阶段5_文稿与投稿包.md)** | W9–W12（07.27–09.15） | 文稿是否自洽可投？ | **Draft v1**、**Fig.7**、Abstract、投稿包 | P5–P6 + F4 |

**阶段文档目录**：[phases/README.md](./phases/README.md)

---

## 3. AI 执行节奏（自行安排）

| 阶段 | 周期 | 工期 | 论文产出 |
|------|------|------|----------|
| 1 | 06.01–06.07 | 7d | §3、Fig.1 |
| 2 | 06.08–06.21 | 14d | §4.1、Fig.3 |
| 3 | 06.22–07.05 | 14d | §4.2–4.3、Fig.2 |
| 4 | 07.06–07.26 | 21d | §5.1–5.2、Fig.5–6、M6 |
| 5 | 07.27–09.15 | 50d | Draft v1、投稿 |

```
阶段1 ──► 阶段2 ──► 阶段3 ──► 阶段4 ──► 阶段5
系统基座   Edge IQA   闭环路由   主实验+M6   文稿投稿
7d         14d        14d        21d         50d
```

**并行策略**：

- 阶段 1 末：franka API 与 paper1 目录 **同时** 可演示。  
- 阶段 2：scorer 单测与 vision API **同 PR 周期** 合入。  
- 阶段 3：LangGraph 与 `paper1_closed_loop.sh` **联调日** 定为阶段唯一硬门禁。  
- 阶段 4：`run_matrix`（离线）与 `paper1_run_m6.sh`（辅轨）**不混 CSV**。  
- 阶段 5：数字冻结后再写 Abstract（含 M1/M2 一句）。

---

## 4. 学生最小介入清单（每阶段 ≤2 项）

| 阶段 | 学生仅做 |
|------|----------|
| 1 | 确认 `doctor/paper1` 存在；跑通 `testall.sh` |
| 2 | 可选：提供 ≥100 张舌象 val 子集路径 |
| 3 | 可选：RViz 微调 `poses.yaml` 两档关节角 |
| 4 | 确认主实验 CSV 与论文表格人工 spot-check |
| 5 | 润色/投稿系统提交、导师签字 |

其余编码、脚本、图、LaTeX 节草稿由 **AI 完成**。

---

## 5. 仓库与分支约定

| 仓库 | 分支模式 | 说明 |
|------|----------|------|
| `franka_ros2` | `paper1/phase-{1..5}-*` | 每阶段一个 PR，合并前跑 `colcon build` + `pytest franka_api_server` |
| `doctor/paper1/` | 与本仓同 PR | 算法、实验、LaTeX 均在本仓库 |

**工件统一路径（paper1）**：

```
experiments/debug/          # 截图、单张 PNG
experiments/logs/           # *.jsonl
experiments/results/        # *.csv（main_* 与 franka_m6_* 分离）
figures/                    # fig*.pdf
latex/sections/             # 各节 tex
```

---

## 6. 指标—阶段映射

| 指标 | 阶段 | 主轨/辅轨 |
|------|------|-----------|
| —（架构） | 1 | 叙述 |
| IQA 延迟、τ | 2 | 算法 |
| 路由三分支、JSONL 字段 | 3 | 算法+辅轨 |
| **M1** RTT p50/p95 | 4 | **主轨** CSV |
| **M2** 有效帧率 | 4 | 主轨 |
| **M3** 重试率 | 4 | 主轨 |
| **M4** τ 消融 | 5 | 主轨 |
| **M5** 跨集 | 2/5 | 主轨 |
| **M6** 闭环 RTT 趋势 | 4 | **辅轨** franka |

---

## 7. 风险与 AI 兜底

| 风险 | AI 兜底 |
|------|---------|
| `doctor/paper1` 缺失 | `check_paper1_env.sh` 硬失败；阶段 1 已提供目录骨架 |
| TCM 全量未下完 | `datasets/vision/tcm-tongue/splits/` 用 500–1000 张种子集 + 合成 blur/exposure |
| Gazebo 相机不稳 | 阶段 3 前允许 **数据集 PNG 注入** `capture_001.png`，Gazebo 作 Supp. |
| 真机不可用 | 全文基于 fake HW + 离线延迟模型 |

---

## 8. 阶段验收闸门（总表）

- [x] **阶段 1**：Fig.1 SVG + OpenAPI 含 skills/vision 占位 + `PAPER1_MODE` 生效  
- [x] **阶段 2**：Fig.3 + API p95&lt;30ms + §4.1 tex 草稿  
- [x] **阶段 3**：Fig.2 + `run_001.jsonl` ≥10 行 + §4.2–4.3 tex  
- [x] **阶段 4**：`main_seed*.csv` + Fig.5–6 + `franka_m6_rtt.csv` + Fig.S1（见 [verification/阶段4_验证报告.md](./verification/阶段4_验证报告.md)）  
- [x] **阶段 5**：`latex/main.pdf` + 投稿目录 + `REPRODUCE_franka.md`（见 [verification/阶段5_验证报告.md](./verification/阶段5_验证报告.md)）

---

## 9. 文档索引

| 文档 | 用途 |
|------|------|
| [README.md](./README.md) | V19 目录导航；图表采用表格/ASCII（无 Mermaid） |
| [verification/阶段1-2_验证总览.md](./verification/阶段1-2_验证总览.md) | **阶段 1–2 自动验证结论** |
| **本文档** | AI 总纲与日历 |
| [phases/](./phases/) | 各阶段科研安排（可独立执行） |
| [franka_ros2_技术实现方案.md](./franka_ros2_技术实现方案.md) | 文件级实现细节 |
| [franka_ros2_研发任务清单.md](./franka_ros2_研发任务清单.md) | 原 Sprint 清单（已由阶段计划 supersede，作对照） |
| [franka_ros2_优化改进计划.md](./franka_ros2_优化改进计划.md) | 范围与原则 |

---

## 10. 立即下一步（阶段 1 启动）

1. AI：实现 `PAPER1_MODE`、`poses.yaml`、vision 占位、paper1 目录骨架。  
2. 学生：执行 `bash scripts/check_paper1_env.sh` 与 `testall.sh`，反馈日志。  
3. AI：产出 Fig.1 架构图（`doctor/paper1/figures/` 或 franka 镜像路径）。

*阶段 1 详细任务见 [阶段1_系统基座与架构证据.md](./phases/阶段1_系统基座与架构证据.md)。*
