# doctor/ 目录结构与说明

`doctor/` 是本仓库的**科研算法模块**，与 ROS 2 机器人执行层（`franka_api_server` 等）同仓但独立部署。当前包含论文 I（Edge-IQA + LangGraph，云边协同舌象闭环采集）的全部代码、实验、LaTeX 源文件及投稿材料。

---

## 目录树

```
doctor/
├── README.md                     # 顶层索引（指向 paper1/ 和 datasets/）
├── datasets/                     # 数据集占位目录（阶段 0 起）
│   └── .gitkeep
└── paper1/                       # 论文 I：Edge-IQA + LangGraph
    ├── README.md                 # 论文 I 总览、目录映射、快速启动
    ├── REPRODUCE.md              # 所有离线实验的可复现步骤
    ├── requirements-paper1.txt   # Python 依赖清单
    ├── paper1-overleaf.zip       # Overleaf 项目快照（LaTeX 导出）
    ├── datasets/                 # 论文 I 私有数据集占位
    │   └── .gitkeep
    ├── edge_iqa/                 # Phase 2 — 边侧图像质量评估
    ├── langgraph_router/         # Phase 3 — 置信度感知路由
    ├── sim/                      # 网络/机器人延迟仿真模型
    ├── experiments/              # 所有实验代码、配置、结果
    ├── figures/                  # 论文图表与生成脚本
    ├── latex/                    # LaTeX 论文源文件（中英双语）
    ├── scripts/                  # 工具脚本
    ├── tests/                    # 额外测试
    ├── patent/                   # 专利交底书草稿
    └── submission/               # 投稿材料包
```

---

## 顶层目录

### `README.md`
- 顶层索引，映射 `paper1/`（论文 I 代码/实验/LaTeX）和 `datasets/`（数据集占位）
- 定义环境变量 `PAPER1_ROOT=<franka_ros2>/doctor/paper1`

### `datasets/`
- **作用**：数据集存储占位目录
- 当前只有 `.gitkeep`，供后续存放与 paper1 实验共用的数据集文件

---

## `paper1/` — 论文 I 主目录

论文 I 标题：**Edge-IQA + LangGraph：云边协同舌象闭环采集**。核心思路是在 Franka FR3 机械臂侧（边缘端）运行轻量级图像质量评估器，根据质量分数 `Q_img` 和重试预算 `K` 决定：上传云端、边缘重采样、或安全中止。

### `README.md`
- 论文 I 总览：各阶段路径映射、快速启动命令、与 `franka_api_server` 的关系说明

### `REPRODUCE.md`
- **可复现指南**：Table II、Fig.5-7、M5 跨数据集验证、PDF 构建等所有离线实验的分步指令

### `requirements-paper1.txt`
- Python 依赖（锁定版本）：`numpy==1.26.4`, `Pillow==10.4.0`, `matplotlib==3.8.4`, `httpx==0.27.2`, `pytest==8.2.2`, `PyYAML==6.0.1`

### `paper1-overleaf.zip`
- Overleaf 项目导出快照（LaTeX 源码）

---

### `edge_iqa/` — Phase 2：边侧图像质量评估

轻量级、CPU 友好的图像质量评分模块，运行在边缘端（机器人侧计算机）。

| 文件 | 作用 |
|------|------|
| `__init__.py` | 包标记 |
| `__main__.py` | 入口点：`python -m edge_iqa` → 调用 `cli.main()` |
| `cli.py` | **CLI 接口**：`python -m edge_iqa.cli --image PATH --json --resize 512`，调用 `compute_q()` 输出结果 |
| `scorer.py` | **核心模块**。公式：`Q_img = 0.65 * sharpness + 0.35 * exposure`。<br>• sharpness：拉普拉斯方差（向量化加速）<br>• exposure：偏离中灰度 (0.5) 的惩罚<br>• 输出 `ScorerResult`：含 `q_img`、`blur/underexposed/overexposed/poor_exposure` 标志<br>• 实测 p95 延迟约 9.6ms（512px） |
| `tests/` | 单元测试：验证清晰图比模糊图 >= 0.2、模糊标志检测、CLI JSON 输出 |

---

### `langgraph_router/` — Phase 3：置信度感知路由

实现 LangGraph 兼容的决策逻辑：基于 `Q_img`、阈值 `tau` 和重试预算 `K` 三路路由。

| 文件 | 作用 |
|------|------|
| `__init__.py` / `__main__.py` | 包标记与入口（→ `run.main()`） |
| `state.py` | **`TrialState`** TypedDict：一次试验循环的全部字段（图像路径、质量分数、标志位、重试计数、路由决策、时间戳、延迟） |
| `routing.py` | **路由函数**（19 行）：<br>• `q_img >= tau` 且重试未耗尽 → `upload_cloud`<br>• `q_img < tau` 且仍有重试次数 → `resample_edge`<br>• `retry_count > K` → `fail_safe` |
| `graph.py` | **试验执行图**：`run_trial()` 实现 capture → IQA → route 单次循环，支持可选 API 客户端连接真实机器人 |
| `run.py` | **CLI 运行器**：`python -m langgraph_router.run --trials 10 --log ... --tau 0.505 --K 2`，支持 JSONL 日志记录和真实机器人集成 |

---

### `sim/` — 仿真与延迟建模

离线仿真模型，用于实验中的延迟组件采样。

| 文件 | 作用 |
|------|------|
| `NETEM.md` | 网络延迟模型文档（各组件延迟分布说明） |
| `latency_model.py` | **`LatencyConfig`** 数据类 + 3 个采样函数：<br>• `sample_edge_iqa_ms()` — 高斯分布，μ=9, σ=2<br>• `sample_resample_ms()` — 对数正态分布，p50≈50ms<br>• `sample_cloud_upload_ms()` — 均匀分布 50-550ms |
| `franka_bridge/` | **`FrankaApiClient`** — HTTP 客户端，通过 `httpx` 调用 `franka_api_server`：<br>• `evaluate_image()` → POST `/vision/evaluate`<br>• `go_to_skill()` → POST `/motion/skills/{name}`<br>• `capture_image()` → 调用技能后采集<br>• 从环境变量 `FRANKA_API_BASE`、`FRANKA_API_KEY` 读取配置 |

---

### `experiments/` — 所有实验代码

#### 配置文件

| 文件 | 作用 |
|------|------|
| `configs/main_exp.yaml` | 主实验 (M1-M3) 配置：3 个种子、5 个基线 (B0-B4)、500 帧/基线、tau=0.505、K=2、质量混合 50% 清晰/50% 模糊 |
| `configs/ablation_tau.yaml` | tau 消融实验 (M4) 配置：单种子、B2 基线、500 帧、扫描 tau ∈ [0.35, 0.45, 0.505, 0.55, 0.65] |

#### 实验运行脚本

| 文件 | 作用 |
|------|------|
| `run_matrix.py` | **核心离线仿真**：定义 5 个基线 B0-B4：<br>• B0 = 无 IQA 直接上传（朴素方案）<br>• B1 = IQA 评估但始终上传<br>• B2 = IQA + 置信度路由（**本文提出方法**）<br>• B3 = B2 + 学习质量提升<br>输出：逐种子摘要 CSV + 帧级详情 CSV + `table_ii.json` |
| `run_ablation_tau.py` | tau 消融扫描（M4），输出 `ablation_tau.csv` |
| `summarize_m6.py` | 处理 M6 辅助轨 JSONL 日志 → `franka_m6_rtt.csv` + `franka_m6_summary.json` |
| `cross_dataset_report.py` | M5 跨数据集验证：计算合成图像质量分数与真值标签的 Spearman 相关系数，输出 `cross_tcm_fd.csv/.json` |

#### Edge-IQA 校准与基准

| 文件 | 作用 |
|------|------|
| `edge_iqa/calibrate_tau.py` | 从验证集校准阈值 tau：计算清晰/模糊图像中位数质量分数，取中点（钳制在 [0.45, 0.65]）。输出 `calibration_val.csv` 和 `recommended_tau.json` |
| `edge_iqa/latency_benchmark.py` | Edge-IQA CPU 延迟基准测试：512px 分辨率下运行 100 轮，报告 mean/p50/p95/p99/max。验证 p95 < 30ms。实测 ~8.2ms mean, ~9.6ms p95 |

#### 报告生成器

| 文件 | 作用 |
|------|------|
| `reports/build_table_ii.py` | 聚合 3 个种子结果，生成 LaTeX 表格片段 → `latex/sections/table_ii.tex` |
| `reports/build_m6_trend.py` | 对比 M6 辅助轨与 M1 B2，生成叙事性 Markdown 报告 `m6_vs_m1_trend.md` |

#### 实验结果摘要

| 文件 | 作用 |
|------|------|
| `results/recommended_tau.json` | 校准阈值 `tau=0.505`（清晰中位数=0.819，模糊中位数=0.191，n=240） |
| `results/table_ii.json` | **核心结果**：B0 有效率 ~0.49, B1 ~0.50, B2 ~0.99, B3 = 1.0；B2 p50 ~365ms vs B0 ~398ms |
| `results/ablation_tau.csv` | Tau 消融结果 |
| `results/franka_m6_summary.json` | M6 真实机器人闭环跟踪：n=50, p50=7.38ms, p95=8.39ms |
| `results/cross_tcm_fd.json` | 跨数据集 Spearman 相关系数 ρ=0.7513 |
| `results/main_seed{0,1,2}.csv` | 各种子各基线汇总指标 |
| `results/main_seed{0,1,2}_detail.csv` | 各种子帧级详情 |

#### 合成数据

| 路径 | 作用 |
|------|------|
| `synthetic/clear/` | 120 张合成"清晰"舌象（RGB, 512×512） |
| `synthetic/blur/` | 120 张合成"模糊"舌象（同上 + 高斯模糊半径 2.5-5.0） |
| `splits/val.json` | 验证集划分（包含全部 240 张图像及标签） |
| `debug/sample_clear.png` | 调试用示例清晰图 |

---

### `figures/` — 论文图表

| 文件 | 作用 |
|------|------|
| `fig1_system_overview.pdf/.svg` | **图 1**：系统架构图（设备 → 边缘 → 云端三层架构） |
| `fig2_routing_flow.pdf/.svg` | **图 2**：路由流程图（capture → IQA → route → upload/resample/fail） |
| `fig5_rtt_cdf.pdf` | **图 5**：端到端 RTT 累计分布（B0-B3 对比） |
| `fig6_valid_rate.pdf` | **图 6**：各基线有效率柱状图 |
| `fig7_ablation_tau.pdf` | **图 7**：tau 消融（有效率 + RTT 双轴） |
| `fig_iqa_hist.pdf/.svg` | **图 3**：清晰 vs 模糊质量分数直方图 |
| `fig_s1_franka_rtt.pdf` | **图 S1**：M6 辅助轨 RTT 直方图 |
| `fig1_caption.md` | 图 1 标题草稿 |
| `plot_main.py` | 生成 Fig.5 + Fig.6 |
| `plot_ablation_tau.py` | 生成 Fig.7 |
| `plot_iqa_hist.py` | 生成 Fig.3（含无 matplotlib 的 SVG 后备方案） |
| `plot_fig2_routing.py` | 生成 Fig.2 SVG/PDF |
| `plot_m6_rtt.py` | 生成 Fig.S1 |

---

### `latex/` — LaTeX 论文源文件

| 文件 | 作用 |
|------|------|
| `main.tex` / `main.pdf` | 英文手稿 |
| `main-zh.tex` / `main-zh.pdf` | 中文翻译手稿 |
| `references.bib` | 参考文献库 |
| `sections/` | 模块化 LaTeX 章节：00_abstract 至 07_supplementary，含 table_ii.tex |
| `sections/zh/` | 所有章节的中文翻译 |

---

### `scripts/` — 工具脚本

| 文件 | 作用 |
|------|------|
| `synth_degrade.py` | **合成图像生成器**：生成 120 清晰 + 120 模糊椭圆舌象（Perlin 噪声 + 高斯模糊），输出到 `experiments/synthetic/`，同时生成 `splits/val.json` |
| `gen_fig1_pdf.py` | 将 `fig1_system_overview.svg` 转为 PDF（使用 cairosvg，无依赖时降级） |

---

### `tests/` — 额外测试

| 文件 | 作用 |
|------|------|
| `tests/test_routing.py` | 路由 `route()` 函数的 4 个单元测试（upload、resample、fail_safe、边界条件），无 API/ROS 依赖 |

---

### `patent/` — 专利交底书

| 文件 | 作用 |
|------|------|
| `edge_iqa_routing_disclosure.md` | **专利交底书草稿**（中文）。4 条权利要求：<br>1. 基于拉普拉斯锐度 + 曝光的边侧舌象 IQA<br>2. 基于 Q_img、tau、K 的三路路由<br>3. 云端-边缘-设备闭环系统（FastAPI + 子进程 IQA + LangGraph 状态机 + JSONL 日志）<br>4. 从属权利要求：tau 校准、预定义 FR3 关节技能重采样 |

---

### `submission/` — 投稿材料

| 文件 | 作用 |
|------|------|
| `RA-L_20260529/README.md` | 投稿包说明（PDF 拷贝、参考文献清单、脱敏 JSONL 位置说明） |
| `RA-L_20260529/cover_letter.md` | 投稿信草稿（致 RA-L/RCIM），突出贡献：轻量 IQA (p95<10ms)、可审计路由、B2 vs B0 改进 |
| `RA-L_20260529/log.md` | 投稿检查清单：一致性校验、摘要是数字核对、无原始患者图像、DCO/作者/基金、查重/润色 |
| `RA-L_20260529/manuscript.pdf` | 编译好的英文手稿 PDF |
| `RA-L_20260529/manuscript-zh.pdf` | 编译好的中文手稿 PDF |

---

## 与 `franka_api_server` 的关系

`doctor/paper1/` 中的算法模块通过 `franka_api_server`（`franka_api_server/franka_api_server/services/paper1_iqa.py` 和 `routers/vision.py`）暴露为 HTTP API：

| 算法模块 | API 端点 | 调用方式 |
|----------|----------|----------|
| `edge_iqa/scorer.py` | POST `/api/v1/vision/evaluate` | 子进程 `python -m edge_iqa.cli --json --resize 512` 或直接 import |
| `langgraph_router/` | POST `/api/v1/motion/skills/{name}` | 通过 `FrankaApiClient` HTTP 调用 |

环境变量 `PAPER1_ROOT` 指向 `doctor/paper1`，供 `franka_api_server` 定位算法脚本。

---

## 关键指标汇总

| 指标 | 值 | 说明 |
|------|-----|------|
| Edge-IQA p95 延迟 | ~9.6ms (512px) | CPU 端侧推理，实测值 |
| 推荐阈值 tau | 0.505 | 校准集清晰/模糊中位数中点 |
| B2 有效率 (M2) | ~0.99 | IQA + 路由方案（本文方法） |
| B0 有效率 (M2) | ~0.49 | 朴素直接上传方案 |
| B2 p50 RTT | ~365ms | 端到端延迟（含重试） |
| B0 p50 RTT | ~398ms | 无 IQA 直接上传 |
| 跨数据集 Spearman ρ | 0.7513 | M5 合成图像质量与标签相关性 |
| M6 真实机器人 p50 | 7.38ms | 闭环 IQA + 路由 + 日志（不含云端上传） |
