# Paper I — Online Supplementary Material (RA-L)

> **用途**：RA-L 正文 PDF **最多 8 页**（含图表与参考文献）；附录内容不得写入投稿 PDF，须以外链/仓库形式提供。  
> **正文引用**：在 Discussion / Abstract 中以 `\texttt{doctor/paper1/supplementary/}` 指向本目录。  
> **完整技术稿**：`latex/main.pdf`（20 页 archive 版，含原附录全文）。

## 目录

| 文件 | 内容 |
|------|------|
| [online_walkthrough.md](./online_walkthrough.md) | B2 单帧 walkthrough（原 AP-008 移出正文） |
| 下文 §A–§G | 原 LaTeX 附录（算法、扩展表、NR-IQA、部署、失败模式） |
| [../REPRODUCE.md](../REPRODUCE.md) | 一键复现 |
| [../experiments/results/](../experiments/results/) | JSON/CSV 单一数据出口 |

---

## §A 复现与 Artifact 清单

**一键命令**（仓库根目录）：

```bash
bash scripts/paper1_run_tcm_full.sh
```

**主要 artifact**：

- `experiments/splits/tcm_{train,val,test}.json` — 6,719 张 COCO bbox
- `experiments/results/recommended_tau.json` — ROI 标定（τ_B2=0.465）
- `experiments/results/main_seed{0,1,2}_detail.csv` — 帧级矩阵
- `experiments/results/b3_mobilenet.pt` — B3 权重
- `figures/fig_*.pdf` — 全部论文图

**环境**：Edge-IQA 仅需 NumPy/Pillow；B3 训练需 PyTorch（见 `requirements-paper1.txt`）。

**JSONL 字段（10）**：`trial_id`, `image_path`, `q_img`, `flags`, `retry_count`, `route_decision`, `latency_ms`, `t_capture`, `t_iqa`, `t_route`。

---

## §B 扩展算法

**COCO ROI crop**：union bbox → 8% padding → clamp → crop → 512 resize。

**B3 推理**：ROI crop → 224 normalize → MobileNetV3-Small softmax → $Q_{img}=p_{clear}$。

**B3 训练超参**：MobileNetV3-Small, AdamW $10^{-3}$, batch 64, 5 epochs, val acc 98.34%。

---

## §C 扩展表格（原附录）

### Table III — 学习型 IQA（已在正文 RA-L 版保留）

见 `latex/sections/table_iii.tex`；数值：B3 M2≈0.934, B4 M2≈0.936（3 seeds）。

### 分层 M2（clear vs blur cohort）

见 `latex/sections/table_stratified_m2.tex` 与 `experiments/results/table_ii_bootstrap.json`。

### NR-IQA 基线（BRISQUE / NIQE）

见 `latex/sections/table_nr_iqa.tex`；复现：

```bash
python3 experiments/reports/build_table_nr_iqa.py
python3 experiments/run_matrix_tcm.py --config experiments/configs/main_exp_nr.yaml --tag nr
```

### 延迟模型分量

| 组件 | 值 (ms) |
|------|---------|
| Capture | 5.0 |
| Edge-IQA | $\mathcal{N}(9, 2^2)$ |
| Route | 1.5 |
| Resample (lognormal) | p50 ≈ 50 |
| Cloud upload | U(50, 550) |
| B3 extra | +15–40 |

### Per-seed Table II 分解

| Seed | B2 M1 p50 | B2 M2 | B3 M2 |
|------|-----------|-------|-------|
| 0 | 211.1 ms | 0.610 | 0.944 |
| 1 | 205.6 ms | 0.602 | 0.938 |
| 2 | 208.3 ms | 0.600 | 0.920 |

### LangGraph vs FSM 基准

1000 trials：LangGraph 额外开销 ≈ 3.6 µs/trial（可忽略 vs 9 ms IQA）。

### 路由扩展 quick ablation（60 frames, seed 0）

| Baseline | M1 p50 | M2 | M3 |
|----------|--------|-----|-----|
| B2 fixed τ | 211.3 | 0.600 | 0.417 |
| B2d dynamic τ | 209.0 | 0.550 | 0.467 |
| B2m EMA | 280.4 | **0.650** | 0.417 |
| B2u utility | 205.4 | **0.650** | 0.367 |

---

## §D 符号表

| 符号 | 含义 |
|------|------|
| $Q_{img}$ | Edge-IQA 质量分 [0,1] |
| $\tau$, $\tau_{B2}$ | 路由阈值（0.465 ROI） |
| M1 | 端到端 RTT p50/p95 |
| M2 | 有效帧率 |
| M3 | 重采样率 |
| M5 | Spearman ρ（clear vs blur） |
| M6 | Franka 辅轨 RTT 趋势 |

---

## §E 部署与网关

**环境变量**：`PAPER1_MODE`, `PAPER1_ROOT`, `PAPER1_IQA_SUBPROCESS`, `PAPER1_VISION_THRESHOLD_TAU`（见 `docs-zh/paper1/V19/ENV.md`）。

**API**：`/api/v1/vision/evaluate`, `/api/v1/motion/skills/{name}`。

**M6 辅轨**：50 trials FR3 fake HW；Fig.S1 `figures/fig_s1_franka_rtt.pdf`。**不得合并进 Table II**。

---

## §F 失败模式

- **负分离度**：validation 上 min(clear) − max(blur) = −0.541；τ 为 cohort 中位 operating point。
- **B3/τ 尺度耦合**：MobileNet 分数域与 Edge-IQA 不同，需独立标定 τ_B3。
- **示意图**：`figures/fig_failure_modes_schematic.pdf`（脱敏 schematic，无患者原图）。

---

## §G 伦理与局限

- ShezhenV3-COCO 公开语料；**未招募新受试者**；JSONL 无患者标识。
- 合成高斯 blur 未必覆盖真实运动 smear。
- M2 为 scorer 内部指标，非临床质量金标准。
- 生成式 AI 仅辅助英文行文；指标均经 `experiments/results/*.json` 核对。

---

*最后更新：2026-06-04 · 对应 RA-L 投稿包 `submission/RA-L_20260529/manuscript.pdf`（`main-ral.pdf`，7 页，≤8 页上限）*
