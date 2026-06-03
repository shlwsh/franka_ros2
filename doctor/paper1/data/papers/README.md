# 📚 Paper I 相关文献说明清单

> **生成日期**：2026-06-04  
> **论文主题**：*Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging: Edge-IQA and LangGraph Closed-Loop Acquisition*  
> **存储路径**：`doctor/paper1/data/papers/`  
> **文献总数**：15 篇 ｜ **总大小**：65 MB  
> **论文附录 NR-IQA**：BRISQUE / NIQE 基线见 `latex/sections/table_nr_iqa.tex`（同 LangGraph 重采壳）

---

## 一、与论文的主题关联

本清单围绕 Paper I 的五个核心研究方向进行文献组织：

| 方向 | 论文中的对应模块 | 文献数量 |
|------|------------------|----------|
| 🖼️ 无参考图像质量评估（NR-IQA） | Edge-IQA 评分模型 | 7 篇 |
| 🤖 LLM 智能体与工具调用 | LangGraph 路由决策引擎 | 4 篇 |
| 🌐 边缘智能与轻量推理 | 云-边-端协同架构、MobileNet 骨干 | 3 篇 |
| 🔬 超分辨率与感知质量 | 辅助参考 | 1 篇 |

---

## 二、文献详细说明

### 🖼️ 方向一：无参考图像质量评估（NR-IQA）

本方向文献直接支撑论文中 Edge-IQA 模块的设计——在边缘网关上对舌象帧进行实时质量评分，指导 LangGraph 路由器做出上传/重采样/中止决策。

---

#### 1. MUSIQ: Multi-scale Image Quality Transformer

| 项目 | 信息 |
|------|------|
| **文件名** | `2021_Ke_MUSIQ_Multi-scale_Image_Quality_Transformer.pdf` |
| **文件大小** | 5.4 MB |
| **作者** | Junjie Ke, Qifei Wang, Yilin Wang, Peyman Milanfar, Feng Yang |
| **年份** | 2021 |
| **引用量** | ~400 |
| **出处** | arXiv:2108.05997 / ICCV 2021 |
| **DOI** | `10.48550/arXiv.2108.05997` |
| **链接** | [arXiv](https://arxiv.org/abs/2108.05997) |

**概要**：提出多尺度图像质量 Transformer（MUSIQ），通过基于哈希的位置编码处理原始分辨率输入，无需将图像裁剪或缩放到固定尺寸。引入多尺度表征以同时捕捉全局语义和局部失真信息，在 KonIQ-10k、SPAQ 等 NR-IQA 基准上取得 SOTA 结果。

**与论文关系**：Edge-IQA 的核心思想——在不同尺度评估图像质量——可借鉴 MUSIQ 的多尺度策略，但需要轻量化以满足边缘推理 <10ms 的约束。

---

#### 2. CLIP-IQA: Exploring CLIP for Assessing the Look and Feel of Images

| 项目 | 信息 |
|------|------|
| **文件名** | `2023_Wang_Exploring_CLIP_for_Assessing_the_Look_and_Feel_of_.pdf` |
| **文件大小** | 22 MB |
| **作者** | Jianyi Wang, Kelvin C.K. Chan, Chen Change Loy |
| **年份** | 2023 |
| **引用量** | ~250 |
| **出处** | arXiv:2207.12396 / AAAI 2023 |
| **DOI** | `10.48550/arXiv.2207.12396` |
| **链接** | [arXiv](https://arxiv.org/abs/2207.12396) |

**概要**：探索使用 CLIP（Contrastive Language-Image Pre-training）进行图像质量和美学评估。利用反义词提示对（如 "good quality" vs "bad quality"）实现零样本和小样本质量预测，无需大规模 IQA 标注数据。通过提示学习可扩展到多种质量属性评估。

**与论文关系**：CLIP-IQA 的零样本质量评估思路可作为 Edge-IQA 在缺乏舌象专用标注数据时的初始化方案参考；论文中 $\tau_{B2}=0.465$ 的阈值校准也可借鉴其提示对比策略。

---

#### 3. TOPIQ: A Top-down Approach from Semantics to Distortions for Image Quality Assessment

| 项目 | 信息 |
|------|------|
| **文件名** | `2024_Chen_TOPIQ_A_Top-down_Approach_from_Semantics_to_Distor.pdf` |
| **文件大小** | 6.9 MB |
| **作者** | Chaofeng Chen, Jiadi Mo, Jingwen Hou, Haoning Wu, Liang Liao, Wenxiu Sun, Qiong Yan, Weisi Lin |
| **年份** | 2024 |
| **引用量** | ~80 |
| **出处** | arXiv:2308.03060 / IEEE TIP 2024 |
| **DOI** | `10.48550/arXiv.2308.03060` |
| **链接** | [arXiv](https://arxiv.org/abs/2308.03060) |

**概要**：提出自顶向下的 IQA 方法，利用高层语义特征引导低层失真特征的提取。设计了一种跨尺度注意力模块（Cross-Scale Attention），在全参考和无参考两种场景下均实现 SOTA。支持同时评估质量和美学属性。

**与论文关系**：TOPIQ 的语义引导失真检测思路与 Edge-IQA 对舌象 ROI 区域的语义理解需求高度一致——先识别舌体区域，再评估该区域的采集质量。

---

#### 4. HyperIQA: Blindly Assess Image Quality in the Wild Guided by A Self-Adaptive Hyper Network

| 项目 | 信息 |
|------|------|
| **文件名** | `2020_Su_HyperIQA_Blindly_Assess_Image_Quality_in_the_Wild_.pdf` |
| **文件大小** | 2.3 MB |
| **作者** | Shanshan Su, Qingsen Yan, Yu Zhu, Cheng Zhang, Xin Ge, Jinqiu Sun, Yanning Zhang |
| **年份** | 2020 |
| **引用量** | ~350 |
| **出处** | arXiv:2004.05508 / CVPR 2020 |
| **DOI** | `10.48550/arXiv.2004.05508` |
| **链接** | [arXiv](https://arxiv.org/abs/2004.05508) |

**概要**：提出基于超网络（Hyper Network）的盲图像质量评估方法。超网络根据输入图像的语义内容自适应生成质量感知规则，解决了"同一失真在不同语义内容下主观感受不同"的问题。在 LIVE Challenge、KonIQ-10k 数据集上取得领先性能。

**与论文关系**：HyperIQA 的内容自适应评估思路对舌象场景特别有价值——舌苔/舌质等不同区域对"合格"的定义不同，自适应机制可提升 Edge-IQA 对舌象特定内容的评估准确性。

---

#### 5. TReS: Relative Ranking with Transformer for Image Quality Assessment

| 项目 | 信息 |
|------|------|
| **文件名** | `2022_Golestaneh_TReS_Relative_Ranking_with_Transformer_for_Image_Q.pdf` |
| **文件大小** | 286 KB |
| **作者** | S. Alireza Golestaneh, Saba Dadsetan, Kris M. Kitani |
| **年份** | 2022 |
| **引用量** | ~200 |
| **出处** | arXiv:2108.10951 / WACV 2022 |
| **DOI** | `10.48550/arXiv.2108.10951` |
| **链接** | [arXiv](https://arxiv.org/abs/2108.10951) |

**概要**：使用 Transformer 编码器进行 NR-IQA，创新性地引入自一致性相对排序损失（Self-Consistency Relative Ranking Loss），通过学习图像对之间的质量相对排序来提升跨数据集泛化能力。

**与论文关系**：TReS 的相对排序思路可用于 Edge-IQA 的阈值校准——论文中在 572 个验证对上校准 $\tau_{B2}$ 的过程，本质上就是一种相对质量排序。

---

#### 6. PromptIQA: Boosting the Performance and Generalization for No-Reference Image Quality Assessment via Prompts

| 项目 | 信息 |
|------|------|
| **文件名** | `2024_Chen_PromptIQA_Boosting_the_Performance_and_Generalizat.pdf` |
| **文件大小** | 3.2 MB |
| **作者** | Zewen Chen, Haina Qin, Juan Wang, Chunfeng Yuan, Bing Li, Weiming Hu, Liang Wang |
| **年份** | 2024 |
| **引用量** | 新发表 |
| **出处** | arXiv:2403.04993 |
| **DOI** | `10.48550/arXiv.2403.04993` |
| **链接** | [arXiv](https://arxiv.org/abs/2403.04993) |

**概要**：通过提示学习（Prompt Learning）提升 NR-IQA 的性能和泛化能力。设计了面向质量评估的提示机制，使模型能够在不同失真类型和数据集之间保持一致的评估表现，解决了传统 NR-IQA 模型跨域泛化差的问题。

**与论文关系**：PromptIQA 的提示泛化策略可用于解决 Edge-IQA 从通用图像域迁移到舌象专用域时的泛化问题。

---

#### 7. DR.Experts: Differential Refinement of Distortion-Aware Experts for Blind Image Quality Assessment

| 项目 | 信息 |
|------|------|
| **文件名** | `2026_Fu_DRExperts_Differential_Refinement_of_Distortion-Aw.pdf` |
| **文件大小** | 2.9 MB |
| **作者** | Bohan Fu, Guanyi Qin, Fazhan Zhang, Zihao Huang, Mingxuan Li, Runze Hu |
| **年份** | 2026 |
| **引用量** | 新发表 |
| **出处** | OpenAlex / 预印本 |
| **链接** | [OpenAlex](https://openalex.org/) |

**概要**：提出失真感知专家差异化精炼方法用于盲图像质量评估。通过多个失真类型专家网络的协同与差异化训练，实现对不同失真类型（模糊、噪声、压缩等）的精细化质量评估。

**与论文关系**：舌象采集中可能同时存在运动模糊、光照不均、压缩失真等多种质量问题，DR.Experts 的多专家分治策略可为 Edge-IQA 的多失真类型处理提供参考。

---

### 🤖 方向二：LLM 智能体与工具调用

本方向文献支撑论文中 LangGraph 路由器的设计理念——将"推理-决策-行动"的智能体范式应用于机器人采集流程中的路由决策。

---

#### 8. ReAct: Synergizing Reasoning and Acting in Language Models

| 项目 | 信息 |
|------|------|
| **文件名** | `2023_Yao_ReAct_Synergizing_Reasoning_and_Acting_in_Language.pdf` |
| **文件大小** | 619 KB |
| **作者** | Shunyu Yao, Jeffrey Zhao, Dian Yu, Nan Du, Izhak Shafran, Karthik Narasimhan, Yuan Cao |
| **年份** | 2023 |
| **引用量** | ~1,500 |
| **出处** | arXiv:2210.03629 / ICLR 2023 |
| **DOI** | `10.48550/arXiv.2210.03629` |
| **链接** | [arXiv](https://arxiv.org/abs/2210.03629) |

**概要**：提出 ReAct 范式，让 LLM 交替生成推理链（Reasoning Traces）和任务特定动作（Actions），实现推理与行动的协同。在知识密集型和决策密集型任务中显著优于单独的推理或行动方法。

**与论文关系**：LangGraph 路由器的核心就是 ReAct 范式的实例化——根据 Edge-IQA 评分（感知）进行推理（是否满足质量阈值），然后决定行动（云上传/边缘重采样/中止），形成感知-推理-行动的闭环。

---

#### 9. Toolformer: Language Models Can Teach Themselves to Use Tools

| 项目 | 信息 |
|------|------|
| **文件名** | `2023_Schick_Toolformer_Language_Models_Can_Teach_Themselves_to.pdf` |
| **文件大小** | 643 KB |
| **作者** | Timo Schick, Jane Dwivedi-Yu, Roberto Dessi, Roberta Raileanu, Maria Lomeli, Luke Zettlemoyer, Nicola Cancedda, Thomas Scialom |
| **年份** | 2023 |
| **引用量** | ~800 |
| **出处** | arXiv:2302.04761 / NeurIPS 2023 |
| **DOI** | `10.48550/arXiv.2302.04761` |
| **链接** | [arXiv](https://arxiv.org/abs/2302.04761) |

**概要**：训练语言模型自主学习何时调用工具、调用什么工具、以及如何使用工具的返回结果。仅通过少量 API 调用标注即可让 LM 自主习得计算器、搜索引擎、翻译器等外部工具的调用时机和方式。

**与论文关系**：Toolformer 的自主工具调用机制与论文中 LangGraph 路由器调用 Edge-IQA 评分工具、调用 ROS 重采样技能的模式高度一致，为理解智能体如何自主决定调用外部能力提供了理论基础。

---

#### 10. A Survey on Large Language Model based Autonomous Agents

| 项目 | 信息 |
|------|------|
| **文件名** | `2024_Wang_A_survey_on_large_language_model_based_autonomous_.pdf` |
| **文件大小** | 4.2 MB |
| **作者** | Lei Wang, Chen Ma, Xueyang Feng, Zeyu Zhang, Hao Yang, Jingsen Zhang, Zhiyuan Chen, Jiakai Tang, Xu Chen, Yankai Lin, Wayne Xin Zhao, Zhewei Wei, Ji-Rong Wen |
| **年份** | 2024 |
| **引用量** | ~1,093 |
| **出处** | Frontiers of Computer Science, 2024 |
| **DOI** | `10.1007/s11704-024-40231-1` |
| **链接** | [Springer](https://doi.org/10.1007/s11704-024-40231-1) |

**概要**：全面综述基于 LLM 的自主智能体，从构建（Profile、Memory、Planning、Action）、应用（社会仿真、自然科学、工程）和评估三个维度展开。系统性地梳理了智能体的感知-推理-行动-记忆架构。

**与论文关系**：为论文中 LangGraph 闭环架构提供分类学背景——Paper I 中的路由器可被定位为"具备感知（Edge-IQA）和有界重试预算的规划能力"的特定领域自主智能体。

---

#### 11. GPT-4 Technical Report

| 项目 | 信息 |
|------|------|
| **文件名** | `2023_Kalana_GPT-4_Technical_Report.pdf` |
| **文件大小** | 5.1 MB |
| **作者** | OpenAI |
| **年份** | 2023 |
| **引用量** | ~2,339 |
| **出处** | arXiv:2303.08774 |
| **DOI** | `10.4230/lipics.cosit.2024.11` |
| **链接** | [arXiv](https://arxiv.org/abs/2303.08774) |

**概要**：OpenAI GPT-4 大型多模态模型技术报告。展示了 GPT-4 在各种专业和学术基准上的表现，包括通过模拟律师资格考试。讨论了预测性缩放规律、安全对齐和多模态能力。

**与论文关系**：GPT-4 的多模态推理能力是 LangGraph 路由器潜在的升级路径——未来可将舌象直接传入多模态 LLM 进行视觉推理，替代当前的规则化路由逻辑。

---

### 🌐 方向三：边缘智能与轻量推理

本方向文献支撑论文中云-边-端协同架构和 MobileNet 骨干网络的设计——如何在 ARM 边缘设备上以 <10ms 的延迟运行 IQA 推理。

---

#### 12. Edge Intelligence: Paving the Last Mile of AI with Edge Computing

| 项目 | 信息 |
|------|------|
| **文件名** | `2019_Zhou_Edge_Intelligence_Paving_the_Last_Mile_of_Artifici.pdf` |
| **文件大小** | 3.7 MB |
| **作者** | Zhi Zhou, Xu Chen, En Li, Liekang Zeng, Ke Luo, Junshan Zhang |
| **年份** | 2019 |
| **引用量** | ~1,200 |
| **出处** | arXiv:1905.10083 / Proceedings of the IEEE, 2019 |
| **DOI** | `10.48550/arXiv.1905.10083` |
| **链接** | [arXiv](https://arxiv.org/abs/1905.10083) |

**概要**：系统综述边缘智能，定义了从 Cloud Intelligence 到 On-Device Intelligence 的六级分类体系（Level 1–6）。全面覆盖模型压缩、知识蒸馏、早退出策略、分层推理等使 DNN 在边缘高效运行的关键技术。

**与论文关系**：Paper I 的架构对应该综述中的 Level 3–4（边缘推理 + 云端协同）。Edge-IQA 在网关运行轻量推理属于 Edge Intelligence 的典型应用。

---

#### 13. A Survey on Edge Intelligence

| 项目 | 信息 |
|------|------|
| **文件名** | `2021_Xu_A_Survey_on_Edge_Intelligence.pdf` |
| **文件大小** | 4.0 MB |
| **作者** | Dianlei Xu, Tong Li, Yong Li, Xiang Su, Sasu Tarkoma, Tongtong Jiang, Jon Crowcroft, Pan Hui |
| **年份** | 2021 |
| **引用量** | ~500 |
| **出处** | arXiv:2003.12172 / ACM Computing Surveys, 2021 |
| **DOI** | `10.48550/arXiv.2003.12172` |
| **链接** | [arXiv](https://arxiv.org/abs/2003.12172) |

**概要**：从架构、使能技术和应用三个维度综述边缘智能。特别关注计算卸载决策（offloading decision）、模型分割（model partitioning）和缓存策略在边缘部署中的作用。

**与论文关系**：论文中 LangGraph 路由器的"上传/本地重采样/中止"三路决策本质上就是一个计算卸载问题——根据网络延迟和质量评分决定在边缘处理还是推送到云端。

---

#### 14. MobileNetV2: Inverted Residuals and Linear Bottlenecks

| 项目 | 信息 |
|------|------|
| **文件名** | `2018_Sandler_MobileNetV2_Inverted_Residuals_and_Linear_Bottlene.pdf` |
| **文件大小** | 1.5 MB |
| **作者** | Mark Sandler, Andrew Howard, Menglong Zhu, Andrey Zhmoginov, Liang-Chieh Chen |
| **年份** | 2018 |
| **引用量** | ~10,000 |
| **出处** | arXiv:1801.04381 / CVPR 2018 |
| **DOI** | `10.48550/arXiv.1801.04381` |
| **链接** | [arXiv](https://arxiv.org/abs/1801.04381) |

**概要**：提出 MobileNetV2 架构，核心创新是倒残差结构（Inverted Residuals）和线性瓶颈（Linear Bottlenecks）。通过深度可分离卷积大幅降低计算量，在 ImageNet 精度与移动端效率之间取得出色平衡，成为边缘视觉任务的标准骨干网络。

**与论文关系**：论文中 B3/B4 基线使用 MobileNet 推理实现 M2≈0.93 的有效帧率，MobileNetV2 正是 Edge-IQA 轻量化骨干的核心选型依据。论文报告的 p95≈9.6ms CPU 推理延迟也基于此架构。

---

### 🔬 方向四：辅助参考

---

#### 15. OP4KSR: One-Step Patch-Free 4K Super-Resolution with Periodic Artifact Suppression

| 项目 | 信息 |
|------|------|
| **文件名** | `2026_Deng_OP4KSR_One-Step_Patch-Free_4K_Super-Resolution_wit.pdf` |
| **文件大小** | 2.6 MB |
| **作者** | Chengyan Deng, Pengbin Yu, Zhentao Chen, Wei Shen, Kai Zhang, Meng Li, Lunxi Yuan, Xue Zhou, Li Yu |
| **年份** | 2026 |
| **引用量** | 新发表 |
| **出处** | 预印本 |

**概要**：提出无需分块的一步式 4K 超分辨率方法，通过周期性伪影抑制解决扩散模型在高分辨率生成时的重复纹理问题。在 4K 分辨率下实现高质量单步超分辨率推理。

**与论文关系**：辅助参考——超分辨率中的感知质量评估指标与 NR-IQA 共享评测体系，可为 Edge-IQA 的评估标准设计提供跨领域视角。

---

## 三、快速索引表

| # | 方向 | 文件名 | 大小 | 年份 | 引用 |
|---|------|--------|------|------|------|
| 1 | IQA | `2021_Ke_MUSIQ_Multi-scale_Image_Quality_Transformer.pdf` | 5.4M | 2021 | ~400 |
| 2 | IQA | `2023_Wang_Exploring_CLIP_for_...Look_and_Feel_of_.pdf` | 22M | 2023 | ~250 |
| 3 | IQA | `2024_Chen_TOPIQ_A_Top-down_Approach_...Distor.pdf` | 6.9M | 2024 | ~80 |
| 4 | IQA | `2020_Su_HyperIQA_Blindly_Assess_...Wild_.pdf` | 2.3M | 2020 | ~350 |
| 5 | IQA | `2022_Golestaneh_TReS_Relative_Ranking_...Image_Q.pdf` | 286K | 2022 | ~200 |
| 6 | IQA | `2024_Chen_PromptIQA_Boosting_...Generalizat.pdf` | 3.2M | 2024 | 新 |
| 7 | IQA | `2026_Fu_DRExperts_...Distortion-Aw.pdf` | 2.9M | 2026 | 新 |
| 8 | Agent | `2023_Yao_ReAct_Synergizing_...Language.pdf` | 619K | 2023 | ~1,500 |
| 9 | Agent | `2023_Schick_Toolformer_...Themselves_to.pdf` | 643K | 2023 | ~800 |
| 10 | Agent | `2024_Wang_A_survey_on_large_language_model_...autonomous_.pdf` | 4.2M | 2024 | ~1,093 |
| 11 | Agent | `2023_Kalana_GPT-4_Technical_Report.pdf` | 5.1M | 2023 | ~2,339 |
| 12 | Edge | `2019_Zhou_Edge_Intelligence_...Artifici.pdf` | 3.7M | 2019 | ~1,200 |
| 13 | Edge | `2021_Xu_A_Survey_on_Edge_Intelligence.pdf` | 4.0M | 2021 | ~500 |
| 14 | Edge | `2018_Sandler_MobileNetV2_...Linear_Bottlene.pdf` | 1.5M | 2018 | ~10,000 |
| 15 | 辅助 | `2026_Deng_OP4KSR_...Super-Resolution_wit.pdf` | 2.6M | 2026 | 新 |

---

## 四、推荐阅读顺序

### 快速入门（2 小时）
1. **MobileNetV2**（#14）— 理解轻量推理骨干
2. **MUSIQ**（#1）— 理解多尺度 IQA 核心思路
3. **ReAct**（#8）— 理解推理-行动范式

### 深入理解（半天）
4. **Edge Intelligence 综述**（#12）— 边缘推理全景
5. **HyperIQA**（#4）— 内容自适应质量评估
6. **LLM Agent Survey**（#10）— 智能体架构全貌

### 进阶拓展（1-2 天）
7. **CLIP-IQA**（#2）→ **TOPIQ**（#3）→ **PromptIQA**（#6）— IQA 方法演进链
8. **Toolformer**（#9）— 工具调用理论基础
9. **TReS**（#5）→ **DR.Experts**（#7）— IQA 排序与多专家方法

---

> **备注**：所有 PDF 均来自合法开放获取来源（arXiv 预印本或 OA 期刊），元数据索引详见 `papers_index.json`。
