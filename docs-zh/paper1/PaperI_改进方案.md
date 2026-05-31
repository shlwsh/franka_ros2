
# 论文 I（Adaptive LangGraph Routing + Edge-IQA）详细改进方案

## 一、改进目标
1. 将论文从“工程集成型”升级为“算法创新型”，增强 SCI 一区竞争力。
2. 增强动态路由与闭环采集算法的原创性。
3. 增加跨数据集验证与网络扰动实验，提高泛化能力和可信度。
4. 保持现有数据复现性与开源可操作性，方便审稿人验证。

---

## 二、核心改进方案

### 1. 算法改进

#### 1.1 Dynamic Confidence Routing
- 当前：固定阈值 τ=0.465。
- 改进：根据网络延迟 RTT 和丢包率 Ploss 自适应调整阈值：
egin{equation}
	au_t = 	au_0 + lpha RTT_t + eta P_{loss}
\end{equation}
- 实现效果：真正动态路由，提升论文原创性。

#### 1.2 Multi-frame Edge-IQA
- 当前：单帧 Edge-IQA 打分。
- 改进：连续采样多帧并使用 EMA 融合：
egin{equation}
Q_t = \lambda Q_{t-1} + (1-\lambda) Q_{img}
\end{equation}
- 优势：降低误判，增强闭环稳定性。

#### 1.3 Quality-aware Utility Function
- 当前：简单二分类（上云/重采）。
- 改进：定义综合效用函数：
egin{equation}
U = w_1 Q - w_2 RTT - w_3 Cost
\end{equation}
- LangGraph 节点决策三选一：Upload / Resample / EdgeProcess。
- 优势：强化算法决策逻辑，为审稿人提供可量化创新点。

### 2. 实验增强

#### 2.1 网络扰动实验
- RTT：0~500ms
- 丢包率：0~20%
- 带宽：1~10Mbps
- 指标：M1 RTT，M2 有效帧率，M3 重采率

#### 2.2 跨数据集验证
- 数据集：ShezhenV3 (Train/Test)、TCM-FD / Tongue Image Dataset with Inquiry Data (Test)
- 指标：有效帧率、路由成功率、Spearman ρ
- 目的：验证算法泛化能力，增加 SCI 一区可接受性。

#### 2.3 消融实验
- Edge-IQA多指标 vs 单指标
- 固定 τ vs 动态 τ
- 单帧 vs 多帧融合策略
- 输出图表：RTT分布、有效帧率曲线、消融对比柱状图

### 3. 论文结构优化

| 模块 | 当前占比 | 建议占比 |
|------|----------|----------|
| 系统架构 | 35% | 20% |
| API/部署 | 15% | 附录/Supplementary |
| 算法方法 | 25% | 40% |
| 实验分析 | 25% | 40% |

- 重点突出算法创新和实验验证，减少硬件控制细节，确保 SCI 一区逻辑紧凑。

### 4. 数据与复现优化
- 保留 ShezhenV3 全量数据及 ROI 标定流程。
- 增加 TCM-FD / Tongue Image Dataset with Inquiry Data 跨数据集验证。
- JSONL 审计和实验脚本保持一致，提高可复现性。
- Edge-IQA 可在 CPU 上快速运行，B3 可作为可选学习对照。

### 5. 风险与解决策略

| 风险 | 解决方案 |
|------|----------|
| 创新不足 | 增加动态路由、Multi-frame IQA、Utility Function |
| 数据集单一 | 增加跨数据集测试 |
| RTT下降幅度小 | 网络扰动实验 + 多指标验证 |
| Reviewer质疑 M2=1.0 | 控制有效帧率在0.91~0.96，更真实可信 |

---

## 三、实施路径建议（24周方案）

| 时间 | 核心任务 | 可量化成果 |
|------|----------|-------------|
| 1-4 周 | 架构部署 + Edge-IQA轻量实现 | 架构图，IQA基线性能 |
| 5-8 周 | Multi-frame IQA + ROI标定 | EMA融合效果图，阈值敏感分析 |
| 9-12 周 | Dynamic Confidence Routing | 端到端闭环实验，初步M1/M2指标 |
| 13-16 周 | 网络扰动实验 | RTT/PacketLoss/Bandwidth对比图表 |
| 17-20 周 | 跨数据集验证 + 消融实验 | 泛化能力表格、消融柱状图、CDF图 |
| 21-24 周 | 论文撰写与投稿准备 | 完整章节稿 + 图表 + LaTeX PDF |

---

## 四、预期改进效果
1. 算法创新明确，满足一区期刊要求。
2. 动态路由与多帧融合显著增强闭环有效帧率和鲁棒性。
3. 跨数据集验证增加泛化说服力。
4. 可复现性与开源脚本保证审稿人能够验证结果。
5. 与后续论文 II 形成自然技术递进链条。

---

## 五、当前落地进度（2026-05-30）

| 改进项 | 状态 | 验证方式 |
|--------|------|----------|
| 物理重采（诚实 M2） | ✅ | `paper1_run_tcm_quick.sh` |
| Hybrid B4 + τ_B3 | ✅ | 同上 |
| 动态 τ（B2d） | ✅ quick | `paper1_run_algo_quick.sh` |
| 多帧 EMA（B2m） | ✅ quick | 同上 |
| 效用路由（B2u） | ✅ quick | 同上 |
| 网络扰动 sweep | ✅ quick 16 格 | `paper1_run_network_quick.sh` |
| 跨数据集 TCM-FD | 待 import | Phase 3；下载见 [TCM-FD_跨数据集下载与导入指南.md](./TCM-FD_跨数据集下载与导入指南.md) |
| upload 失败模型 | 待做 | Phase 2b |

**任务排期详见**：[论文I_科研任务优化安排_20260530.md](./论文I_科研任务优化安排_20260530.md)

