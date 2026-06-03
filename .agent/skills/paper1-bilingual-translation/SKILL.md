---
name: paper1-bilingual-translation
description: Maintains synchronized English and Chinese LaTeX manuscripts for Paper I (main.tex / main-zh.tex) and applies consistent translation patterns between them
disable-model-invocation: false
---

# Paper I 双语稿翻译与同步技能

本技能用于在 `doctor/paper1/latex` 下维护 Paper I 的中英文 LaTeX 稿件同步（`main.tex` 与 `main-zh.tex`，以及 `sections/*` 与 `sections/zh/*`），并复用本次翻译中总结出的表达与操作技巧。

## 使用时机

- 编辑或新增 Paper I 英文 LaTeX 章节（`sections/*.tex`）时，需要同时维护中文节（`sections/zh/*.tex`）。
- 修改实验数字、表格（尤其是 Table II）或图注，要求中英文数值与叙述保持一致。
- 需要解释如何从 CSV/脚本自动更新论文数字，并保证中英文稿都引用同一组结果。
- 用户显式提到：
  - “main.pdf / main-zh.pdf 同步”
  - “Paper I 中文版/英文版”
  - “翻译论文 I 某一节”

## 目录与文件映射

- 英文主文件：`latex/main.tex`
- 中文主文件：`latex/main-zh.tex`
- 英文各节：`latex/sections/*.tex`
- 中文各节：`latex/sections/zh/*.tex`
- 主结果表：
  - 英文：`latex/sections/table_ii.tex`
  - 中文：`latex/sections/zh/table_ii.tex`

**章节映射：**

- 摘要：`00_abstract.tex` ↔ `zh/00_abstract.tex`
- 引言：`01_intro.tex` ↔ `zh/01_intro.tex`
- 相关工作：`02_related.tex` ↔ `zh/02_related.tex`
- 系统：`03_system.tex` ↔ `zh/03_system.tex`
- Edge-IQA：`04_1_edge_iqa.tex` ↔ `zh/04_1_edge_iqa.tex`
- 路由：`04_2_routing.tex` ↔ `zh/04_2_routing.tex`
- 闭环与 JSONL：`04_3_closed_loop.tex` ↔ `zh/04_3_closed_loop.tex`
- 实验设置：`05_1_setup.tex` ↔ `zh/05_1_setup.tex`
- 主结果：`05_2_main_results.tex` ↔ `zh/05_2_main_results.tex`
- 消融与跨集：`05_3_ablation.tex` ↔ `zh/05_3_ablation.tex`
- 结论：`06_conclusion.tex` ↔ `zh/06_conclusion.tex`
- 补充材料：`07_supplementary.tex` ↔ `zh/07_supplementary.tex`

## 翻译与同步要点

### 1. 术语对照（保持一致）

在中英文稿之间，优先使用以下固定译法，避免来回切换：

- **系统与场景**
  - cloud–edge–device → 云–边–端
  - tele-diagnosis → 远程诊断 / 远程舌诊（视上下文）
  - trial → trial（保留英文）或 “次试验”/“次 trial”（避免误译为“样本”）
  - EMR → 电子病历（EMR）
  - auxiliary track (M6) → 辅轨 M6 / Franka 辅轨

- **算法与模块**
  - Edge-IQA → Edge-IQA（保留英文，并在首次出现时补充“边缘图像质量评估”）
  - LangGraph router → LangGraph 路由器
  - confidence-aware routing → 置信度感知路由
  - skills → skills / 具名 skill / 具名关节位姿
  - fake hardware → 假硬件

- **指标与变量**
  - end-to-end RTT → 端到端 RTT / 端到端时延
  - valid-frame rate (M2) → 有效帧率（M2）
  - retry rate (M3) → 重试率（M3）
  - threshold τ → 阈值 τ
  - budget K → 重试预算 K
  - upload_cloud / resample_edge / fail_safe → upload_cloud / resample_edge / fail_safe（代码标识保留英文，在文字中可译为“上云/边缘重采/fail-safe 中止”）
  - Q_img → 图像质量分数 $Q_{\\mathrm{img}}$

- **统计描述**
  - p50 / median → 中位数 / p50
  - p95 → p95 分位数
  - seed → 随机种子
  - baseline → 基线（B0–B3 保留编号）

### 2. 文风与句型模式

**推荐中文句型：**

- 英文：“We present a cloud–edge–device stack that …”
  - 中文：`本文提出云–边–端架构，用于……`

- 英文：“We study a cloud–edge–device architecture for …”
  - 中文：`本文研究面向 …… 的云–边–端架构。`

- 英文：“The proposed B2 configuration reduces median RTT from A to B while raising valid-frame rate from C to D.”
  - 中文：`所提 B2 相对 B0 将 RTT 中位数从 A 降至 B，有效帧率从 C 提升至 D。`

- 英文：“An auxiliary Franka closed-loop track confirms…”
  - 中文：`Franka 辅轨闭环（若干次 trial）证实……`

**处理中英混排：**

- 保持公式、符号区段原文不动，例如 `$Q_{\\mathrm{img}} = 0.65 S + 0.35 E$`。
- 保留代码标识和路径，用 `\\texttt{}` 包裹，如 `\\texttt{run_matrix.py}`、`\\texttt{experiments/results/main_seed0.csv}`。
- 中文叙述中出现指标名时写作：“有效帧率（M2）”“端到端 RTT 中位数（M1 p50）”。

### 3. 数字与表格同步技巧

- **唯一真值来源**：
  - Table II / M1–M3 数字只信任 `experiments/results/main_seed{0,1,2}.csv` 及脚本 `build_table_ii.py` 的输出。
  - 任何数字修改应先跑脚本，再将新数值应用到：
    - 英文表：`sections/table_ii.tex`
    - 中文表：`sections/zh/table_ii.tex`
    - 摘要定量句与结论中的数字。

- **拷贝表结构，不拷贝数字**：
  - 为中文表格构建时，可复制英文表的 LaTeX 结构，仅将表头文字翻译为中文；数值通过 CSV 确认后粘贴。

- **避免双重手改**：
  - 禁止“先改英文表，再瞄一眼手动改中文表”的工作流；
  - 正确流程：CSV/脚本 → 英文表 → 中文表 → 中英文文字段落。

### 4. 编译与排版注意事项

- 中文稿优先使用 **XeLaTeX + ctex + Fandol 字体**（当前项目已配置 `fontset=fandol`）。
- 允许存在 `Overfull/Underfull hbox` 警告，只要 PDF 正常输出且排版可接受；不要为消除所有 warning 过度改动技术内容。
- 图像文件共享：
  - `fig5_rtt_cdf.pdf`、`fig6_valid_rate.pdf`、`fig7_ablation_tau.pdf`、`fig_s1_franka_rtt.pdf` 等在中英文稿中共用。
  - 只在 caption 与段落描述中切换语言。

## 操作步骤模板

当用户要求“同时更新中英文稿”或修改影响论文内容的逻辑时，可以按以下流程：

1. **定位章节**：确认对应的英文节文件与中文节文件路径。
2. **在英文稿中实现或修改内容**（公式、图表引用、逻辑说明）。
3. **翻译并同步更新中文稿**：
   - 保持章节结构、符号与引用一致；
   - 应用上述术语表与句型模式；
   - 校对所有数字是否与 CSV / 英文稿一致。
4. 如涉及主结果或消融：
   - 运行脚本：`run_matrix.py`、`build_table_ii.py`、`run_ablation_tau.py` 等；
   - 确认中英文表格与图注一致。
5. 需要时建议用户运行：
   - `bash scripts/paper1_build_draft.sh` 以同时生成 `main.pdf` 与 `main-zh.pdf`。

## 示例：同步主结果段落

- 英文（节 `05_2_main_results.tex`）：

> B2 improves M1 p50 and M2 compared to B0 while keeping retry overhead (M3) bounded by $K$.

- 对应中文（节 `zh/05_2_main_results.tex`）：

> B2 在 M1 p50 与 M2 上优于 B0，且重试开销（M3）受 $K$ 约束。

当英文句子结构变动（例如加入新结论、改动数值），务必同步调整中文句子，并重新检查数字与符号。

