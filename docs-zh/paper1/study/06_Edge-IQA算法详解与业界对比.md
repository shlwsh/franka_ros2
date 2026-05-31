# 06 · Edge-IQA 算法详解与业界对比

> **目标**：说清楚 Edge-IQA **怎么实现**、业内 IQA **有哪些路线**、本文算法在**边侧闭环采集**场景下**为何是合理的最优权衡**（而非宣称全面碾压所有 IQA）。

---

## 1. Edge-IQA 实现逐步拆解

### 1.1 代码位置与调用链

| 层级 | 文件 | 作用 |
|------|------|------|
| 核心算法 | `doctor/paper1/edge_iqa/scorer.py` | 计算 Q_img、flags、耗时 |
| ROI 裁剪 | `doctor/paper1/edge_iqa/coco_roi.py` | COCO 舌框并集 + 8% padding |
| B3 学习 IQA | `doctor/paper1/edge_iqa/learned_b3.py` | MobileNetV3-Small 推理 |
| B3 训练 | `doctor/paper1/experiments/edge_iqa/train_b3_mobilenet.py` | train 划分二分类微调 |
| CLI | `doctor/paper1/edge_iqa/cli.py` | 子进程入口 |
| τ 标定 | `doctor/paper1/experiments/edge_iqa/calibrate_tau_tcm.py` | ShezhenV3 val → recommended_tau.json |
| ROI 消融 | `doctor/paper1/experiments/edge_iqa/roi_ablation.py` | 全图 vs 舌区 ROI 对比 |
| 网关桥接 | `franka_api_server/services/paper1_iqa.py` | HTTP → 子进程调用 scorer |
| 单元测试 | `doctor/paper1/edge_iqa/tests/test_scorer.py` | clear/blur 分离、flags、CLI |

**在线调用链**：

```
POST /api/v1/vision/evaluate
  → paper1_iqa.py::evaluate_image_path()
    → subprocess: python -m edge_iqa.cli --image <path> --json
      → scorer.py::compute_q()
```

### 1.2 算法流程（对照源码）

```
输入：RGB 图像 + 可选 COCO bboxes
  │
  ▼
①（可选）COCO 舌框 ROI 裁剪（并集 + 8% padding）
  │
  ▼
② Resize 至 512×512（PIL Bilinear）
  │
  ▼
② 转灰度：gray = 0.299R + 0.587G + 0.114B，归一化到 [0,1]
  │
  ├─► ③ 清晰度 S
  │     离散 Laplacian（5 点模板）：
  │       lap = -4·gray + roll(上) + roll(下) + roll(左) + roll(右)
  │     variance = Var(lap)
  │     S = variance / (variance + 0.002)   ← 经验缩放，clip 到 [0,1]
  │
  └─► ④ 曝光 E
        mean_val = mean(gray)
        E = 1 - |mean_val - 0.5| / 0.5      ← 中灰 0.5 最优，clip 到 [0,1]
  │
  ▼
⑤ 融合：Q_img = 0.65·S + 0.35·E
  │
  ▼
⑥ 导出 flags（可解释规则）
     blur:          S < 0.35
     underexposed:  mean < 0.25
     overexposed:   mean > 0.85
     poor_exposure: exposure < 0.4（且未触发 under/over）
  │
  ▼
输出：{ q_img, flags, t_iqa_ms, sharpness, exposure }
```

### 1.3 伪代码（与论文 Algorithm 1 一致）

```python
def edge_iqa(image):
    gray = resize_to_gray(image, 512)
    S = normalize(laplacian_variance(gray))      # Var(∇²I)
    E = 1 - abs(mean(gray) - 0.5) / 0.5         # 中灰曝光
    Q_img = 0.65 * S + 0.35 * E
    flags = derive_flags(S, E, gray)
    return Q_img, flags
```

### 1.4 关键超参数（硬编码于 scorer.py）

| 参数 | 值 | 含义 |
|------|-----|------|
| `DEFAULT_SIZE` | 512 | 固定输入尺寸 |
| `SHARPNESS_WEIGHT` | 0.65 | 清晰度权重 |
| `EXPOSURE_WEIGHT` | 0.35 | 曝光权重 |
| `BLUR_THRESHOLD` | 0.35 | S 低于此值 → blur |
| `UNDEREXPOSED_THRESHOLD` | 0.25 | 均值低于此 → underexposed |
| `OVEREXPOSED_THRESHOLD` | 0.85 | 均值高于此 → overexposed |

权重 0.65/0.35 的设计意图：机器人舌象采集中，**微动模糊**比轻微曝光偏差更常导致废帧，故清晰度占主导。

### 1.5 实测数值（ShezhenV3 全量 val，ROI 启用）

来源：`experiments/results/recommended_tau.json`、`tcm_calibration_stats.json`（1144 行 = 572 clear + 572 blur）

| 指标 | 全图 | 舌区 ROI（默认） |
|------|------|------------------|
| 清晰 cohort Q_img 中位数 | 0.564 | **0.516** |
| 模糊 cohort Q_img 中位数 | 0.431 | **0.414** |
| 推荐路由阈值 τ | 0.498 | **0.465** |
| 分离度 min(clear)−max(blur) | −0.510 | −0.541 |
| M5 Spearman ρ | — | **0.363**（n=1144） |

> ROI 降低绝对分数并略增 min-max 重叠，但使评分聚焦舌体解剖区；与下游 TCM 分类器关注区一致。详见 `experiments/results/roi_ablation.json`。

### 1.6 延迟 benchmark

来源：`experiments/edge_iqa/latency_benchmark.json`（100 次 @512px CPU）

| 分位 | 耗时 |
|------|------|
| p50 | 8.01 ms |
| p95 | **9.57 ms** |
| p99 | 11.03 ms |
| 验收门槛 | p95 < 30 ms ✅ |

含 HTTP 网关 + 子进程开销的路径延迟约 **~27 ms**（仍低于 35 ms 工程门槛）。

### 1.7 τ 标定流程

```bash
# 1. 生成合成 clear/blur 图像（若无 TCM 数据）
python3 doctor/paper1/scripts/synth_degrade.py

# 2. 在 val 集上跑 scorer，写 calibration_val.csv + recommended_tau.json
python3 doctor/paper1/experiments/edge_iqa/calibrate_tau.py
```

标定逻辑：
1. 对 val.json 中每张图调用 `compute_q()`
2. 分别统计 label=clear 与 label=blur 的 Q_img 中位数
3. τ = (median_clear + median_blur) / 2，clamp 到 [0.45, 0.65]
4. 合成阶段结果：τ = **0.505**；ShezhenV3 主实验见 `calibrate_tau_tcm.py` → **τ_B2 = 0.465**

---

## 2. 业内 IQA 算法分类与代表

IQA（Image Quality Assessment）按**是否需要参考图**分为三大类。本文属于**无参考 NR-IQA**，且进一步约束为**边侧实时门控**，不是通用 MOS（Mean Opinion Score）预测。

### 2.1 全参考 FR-IQA（Full-Reference）

| 算法 | 原理 | 优势 | 局限（相对本文） |
|------|------|------|------------------|
| **PSNR** | 像素 MSE → dB | 极简、确定性 | 需 pristine 参考图；与人眼感知弱相关 |
| **SSIM** | 亮度/对比度/结构相似 | 比 PSNR 更符合感知 | 仍需参考图；采集闭环无参考 |
| **MS-SSIM** | 多尺度 SSIM | 更鲁棒 | 同上 |
| **LPIPS** | 深度特征距离 | 感知质量强 | 需参考图 + GPU 推理 |

**结论**：FR-IQA 在「机器人逐帧采集、无 golden reference」场景下**不可用**。

### 2.2 手工无参考 NR-IQA（Hand-crafted NR-IQA）

| 算法 | 原理 | 典型延迟 | 优势 | 局限（相对本文） |
|------|------|----------|------|------------------|
| **Laplacian 方差** | Var(∇²I) | ~5 ms | 极简、直接反映模糊 | 仅清晰度，忽略曝光 |
| **Tenengrad** | Sobel 梯度能量 | ~5–10 ms | 对焦检测常用 | 同上 |
| **BRISQUE** | 自然场景统计 + SVR | 50–200 ms | 无参考、有文献支撑 | 分数非 [0,1]；难直接设 τ；未建模曝光 |
| **NIQE** | 自然场景 NSS 特征 | 50–150 ms | 完全盲、无需训练数据 | 同上；对医学舌象域偏移未验证 |
| **PIQE** | 块级失真检测 | 30–80 ms | 可检测块效应 | 对 motion blur + 曝光组合弱 |

论文 Related Work 引用 NIQE~\cite{mittal2012niqe} 与深度 NR-IQA~\cite{zhang2018blind} 作为背景。

### 2.3 深度学习 NR-IQA

| 算法/代表 | 原理 | 典型延迟 | 优势 | 局限（相对本文） |
|-----------|------|----------|------|------------------|
| **DB-CNN** (Zhang et al.) | 双分支 CNN | 10–100+ ms | 感知质量 SOTA 之一 | 需 GPU/权重；黑盒；域偏移需重训 |
| **NIMA** | MobileNet + 美学分布 | 20–50 ms | 可输出分布 | 面向自然图/美学，非采集门控 |
| **HyperIQA** | 超网络 + 内容自适应 | 50–200 ms | 内容感知强 | 计算与部署成本高 |
| **MUSIQ** | 多尺度 Transformer | 100+ ms | 多分辨率 | 边缘 CPU 难满足实时 |
| **MobileNet-V3-Small** | 轻量 CNN | 10–30 ms | 精度/速度折中 | 仍依赖模型分发与版本管理 |

### 2.4 本文 B3 基线（真实 MobileNet 训练）

**2026-05-30 更新**：B3 已改为 **ShezhenV3 train 划分上真实训练的 MobileNetV3-Small**：

- 训练脚本：`experiments/edge_iqa/train_b3_mobilenet.py`
- 权重：`experiments/results/b3_mobilenet.pt`
- 推理：`edge_iqa/learned_b3.py`，输出 `Q_img = P(clear|I)`
- 训练数据：5594 张 train 图 ×（清晰 + 合成模糊）各 1，ROI 裁剪后 224×224
- 主矩阵：`run_matrix_tcm.py` 中 B3 使用学习分数，B2 仍用 Edge-IQA

> 此前 `b3_q_boost=+0.08` 仿真加成已废弃；论文主 claim 仍基于可解释 **B2**。

---

## 3. 多维度对比总表

下表比较各路线在**边侧闭环采集门控**任务下的适配度（非通用 IQA 排行榜）：

| 方法 | 复杂度 | 典型 CPU 延迟 | 需 GPU | 可解释 flags | 直接 τ 路由 | 离线/在线同一 scorer | 覆盖 blur+曝光 |
|------|--------|---------------|--------|-------------|------------|---------------------|---------------|
| **Edge-IQA（本文）** | O(HW) | **~10 ms** | 否 | **是** | **是** | **是** | **是** |
| Laplacian-only | O(HW) | ~5 ms | 否 | 部分（仅 blur） | 是 | 是 | 否 |
| BRISQUE / NIQE | O(patch) | 50–200 ms | 否 | 有限 | 需分数映射 | 需额外封装 | 间接 |
| Deep NR-IQA | O(CNN) | 10–100+ ms | 常需 | 否 | 需分数映射 | 需模型服务 | 取决于训练 |
| B3 MobileNet（真实训练） | O(CNN) | 15–40 ms | 可选 | 否 | 是（概率） | 独立模型 | 取决于训练 |

**评分说明**：
- 「直接 τ 路由」= 分数天然落在 [0,1]，且 val 集上 clear/blur 双峰分离，τ 标定有明确几何意义（Fig.3）
- 「离线/在线同一 scorer」= `calibrate_tau.py` 与 `franka_api_server` 调用同一 `scorer.py`，实验可复现

---

## 4. 为何 Edge-IQA 是本文的最优权衡（诚实论证）

**绝不声称**：Edge-IQA 在所有 IQA 精度指标上全面优于深度学习。

**应声称**：在 cloud–edge robotic acquisition gating 的多约束下，Edge-IQA 在以下维度达到 **Pareto 最优权衡**：

### 4.1 任务匹配：门控而非 MOS 排名

本文 IQA 的角色是**路由门控**（Q ≥ τ → 上传；Q < τ → 重拍），不是预测人类主观质量分数。门控任务需要：
- 清晰/模糊 cohort **双峰分离**（Fig.3）
- 单一阈值 τ 可标定、可解释

Edge-IQA 在 ShezhenV3 ROI val 上 clear 中位 **0.516**、blur **0.414**，τ_B2=**0.465**（分离度指标见 `roi_ablation.json`）。

### 4.2 实时约束：边侧 CPU p95 < 30 ms

| 方法 | p95（本文环境） |
|------|----------------|
| Edge-IQA | **9.57 ms** |
| NIQE/BRISQUE | 通常 50 ms 量级及以上 |
| 深度 NR-IQA | 10–100+ ms，常需 GPU |

机器人网关（FastAPI + rclpy 同进程）需避免 GIL 争用，故 IQA 以**子进程**运行；延迟预算紧张，O(HW) 手工算子最稳妥。

### 4.3 可解释性与临床审计

JSONL 轨迹含 `flags: ["blur"]` 等字段，导师/审稿人/临床工程师可直接理解「为何重拍」。深度模型只能给出黑盒分数，难以写入 Supplementary 样例说明。

### 4.4 部署独立性

- 无 GPU、无模型权重文件、无 ONNX/Torch 依赖链
- 仅 NumPy + PIL，与 `doctor/paper1` 算法边界一致（不进 ROS 包）
- 同一 `scorer.py` 用于离线实验与在线 API，**主表数字与辅轨演示同源**

### 4.5 采集失效模式覆盖

机器人舌象采集的主要废帧原因：
1. **微动模糊** → Laplacian 方差 S 直接建模
2. **曝光漂移**（过亮/过暗）→ 中灰曝光 E 直接建模

通用 NR-IQA（NIQE/BRISQUE）针对自然场景统计，**未显式分离**这两种采集侧失效模式。

### 4.6 与 B3 的边界（Table II）

| Baseline | M2 有效帧率 | M1 p50 (ms) | 说明 |
|----------|-------------|-------------|------|
| **B2（本文主方法）** | **0.604** | **208.3** | 可解释 Edge-IQA + 物理重采 |
| B3（MobileNet @ τ_B2） | **0.934** | 345.6 | 学习排序强，RTT 高 |
| B4（Hybrid） | **0.936** | 343.1 | Tier-A/B 混合 |

**主 claim 基于 B2**：最低 RTT 中位数 + 可审计 flags + 统一 τ_B2 标定。B3/B4 适合「有效率优先、可接受边侧算力」的部署变体。

---

## 5. 与 Fig.3 / 实验数据的对应

| 工件 | 路径 | 关联 |
|------|------|------|
| Fig.3 直方图 | `figures/fig_iqa_hist.pdf` | clear/blur Q_img 分布 + τ 分界线 |
| 标定 CSV | `experiments/results/calibration_val.csv` | 240 行逐图 Q_img |
| τ JSON | `experiments/results/recommended_tau.json` | τ_B2=**0.465** |
| 延迟 JSON | `experiments/edge_iqa/latency_benchmark.json` | p95=9.567 ms |
| 单测 | `edge_iqa/tests/test_scorer.py` | mean_clear − mean_blur > 0.2 |

---

## 6. 导师高频追问

### Q1：为何不用 NIQE 或 BRISQUE？它们也是无参考、不需要 GPU。

**答**：NIQE/BRISQUE 输出非 [0,1] 的 general-purpose 质量分数，需额外映射才能设路由阈值 τ；延迟通常 50 ms 量级，高于本文 p95≈10 ms 预算；且未显式输出 blur/exposure flags。本文任务需要**可阈值化 + 可审计**，Edge-IQA 更贴合。

### Q2：为何不用深度学习 IQA？B3 的 M2 不是更高吗？

**答**：B3 为 **真实 MobileNetV3-Small**（98.3% val acc）。全量 M2 **0.934 > B2 0.604**，但 M1 高约 135 ms。主结论仍基于可解释 B2；Table III 报告 B3/B3t/B4 供选型参考。

### Q3：Edge-IQA 在真实 TCM 数据上验证了吗？

**答**：τ_B2 在 ShezhenV3 val（ROI，n=1144）标定；M5 Spearman **ρ=0.363**；主矩阵在 553 张 test 上 3 seeds 全量重放。跨集 TCM-FD 导入见 [TCM-FD_跨数据集下载与导入指南.md](../TCM-FD_跨数据集下载与导入指南.md)。

### Q4：0.65/0.35 权重怎么定的？能否学习？

**答**：当前为固定经验权重，清晰度优先于曝光（采集微动模糊更常见）。V19 大纲曾提 val 集 logistic 拟合，**当前实现未做**；可作为 future work，不改变主 claim。

### Q5：只用 Laplacian 不够吗？为什么要加曝光 E？

**答**：Laplacian-only 只能检测模糊，无法识别过曝/欠曝废帧。舌象采集光照变化时，清晰但曝光异常的帧仍会污染云端；E 项以低成本补齐这一失效模式。

---

## 7. 一句话总结（答辩用）

> Edge-IQA 在**边侧 CPU 实时、可阈值路由、可解释 flags**约束下针对 blur+exposure 失效模式做工程权衡；全量矩阵中 **B2** 低 RTT + 可审计，**B3/B4** 高 M2 可选。

---

**上一篇** ← [05_导师拷问速答.md](./05_导师拷问速答.md)  
**返回目录** → [README.md](./README.md)
