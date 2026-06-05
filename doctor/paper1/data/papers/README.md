# Paper I 文献本地库说明

> **更新**：2026-06-04（scholar-search 补下载 + 审计）  
> **目录**：`doctor/paper1/data/papers/`  
> **本地 PDF**：**18** 篇 ｜ **RA-L 正文引用 PDF 覆盖**：**6 / 11**  
> **真实性唯一依据**：`latex/references.bib`  
> **对照表**：[`cite_audit.json`](cite_audit.json) · [`cite_key_map.json`](cite_key_map.json)  
> **下载工具**：`.agent/skills/scholar-search/`（仅合法 OA / arXiv）

---

## 核心结论（请先读）

| 问题 | 答案 |
|------|------|
| **RA-L 正文引用了多少篇？** | **11** 个 `\cite{...}` 键 |
| **其中本地已有可核对 PDF？** | **6 / 11**（55%） |
| **是否「全部引用都已下载」？** | **否**。5 条无合法 OA PDF，须用 **DOI 在线核验** |
| **如何保证引用真实？** | 以 **`references.bib`** 为准；PDF 须与 bib 一致，**禁止**用无关论文顶替 cite 键 |

**2026-06-04**：scholar-search 新下载 4 篇（含 `moore2021ros2` arXiv 预印本）+ 3 篇补充 OA；删除错误 GPT-4 PDF。

---

## 一、RA-L 投稿稿正文引用对照（`sections/ral/*.tex`）

以下 11 条为 **7 页投稿 PDF** 中实际出现的引用（2026-06-04 扫描）。

| cite 键 | 题名（摘自 `references.bib`） | DOI | 本地 PDF |
|---------|--------------------------------|-----|----------|
| `zhang2020tongue` | Automatic tongue diagnosis: a survey | [10.1007/s10462-019-09735-6](https://doi.org/10.1007/s10462-019-09735-6) | ❌ 未下载 |
| `qi2016tongue` | Tongue image analysis for disease diagnosis | [10.1016/j.patcog.2016.01.017](https://doi.org/10.1016/j.patcog.2016.01.017) | ❌ 未下载 |
| `moore2021ros2` | Robot Operating System 2: Design, Architecture, and Uses in the Wild | [10.1126/scirobotics.abm6074](https://doi.org/10.1126/scirobotics.abm6074) | ✅ `2022_Macenski_Robot_Operating_System_2_...pdf`（**arXiv:2204.09222 预印本**，与期刊稿对应） |
| `chitta2009moveit` | MoveIt! | [10.1109/MRA.2011.2181749](https://doi.org/10.1109/MRA.2011.2181749) | ❌ 未下载 |
| `mittal2012niqe` | Making a "completely blind" image quality analyzer (NIQE) | [10.1109/LSP.2012.2186026](https://doi.org/10.1109/LSP.2012.2186026) | ❌ 未下载 |
| `kang2017neurosurgeon` | Neurosurgeon: Collaborative Intelligence Between the Cloud and Mobile Edge | [10.1145/3037697.3037728](https://doi.org/10.1145/3037697.3037728) | ❌ 未下载 |
| `su2020hyperiqa` | HyperIQA | [10.1109/CVPR42600.2020.00372](https://doi.org/10.1109/CVPR42600.2020.00372) | ✅ `2020_Su_HyperIQA_...pdf` |
| `wang2023clipiqa` | Exploring CLIP for Assessing the Look and Feel of Images (CLIP-IQA) | [10.1609/aaai.v37i2.25353](https://doi.org/10.1609/aaai.v37i2.25353) | ✅ `2023_Wang_Exploring_CLIP_...pdf` |
| `zhou2019edge` | Edge Intelligence: Paving the Last Mile… | [10.1109/JPROC.2019.2918951](https://doi.org/10.1109/JPROC.2019.2918951) | ✅ `2019_Zhou_Edge_Intelligence_...pdf` |
| `sandler2018mobilenetv2` | MobileNetV2 | [10.1109/CVPR.2018.00474](https://doi.org/10.1109/CVPR.2018.00474) | ✅ `2018_Sandler_MobileNetV2_...pdf` |
| `yao2023react` | ReAct | [10.48550/arXiv.2210.03629](https://doi.org/10.48550/arXiv.2210.03629) | ✅ `2023_Yao_ReAct_...pdf` |

**仍未下载（5 条）— 原因与建议**

| cite 键 | 原因 | 本地替代（仅背景阅读，**不能替代引文**） |
|---------|------|----------------------------------------|
| `zhang2020tongue` | Springer AI Review，无 OA PDF | `2024_Zhang_Qibo_...pdf`（TCM LLM，arXiv） |
| `qi2016tongue` | Pattern Recognition 付费墙 | 同上 |
| `chitta2009moveit` | IEEE RAM 短文，无 OA | — |
| `mittal2012niqe` | IEEE SPL，Unpaywall 无 PDF | `2012_Mittal_No-Reference_...pdf`（**BRISQUE** arXiv:1206.4210，附录 NR-IQA 同族方法） |
| `kang2017neurosurgeon` | ACM ASPLOS，无合法 OA PDF；勿使用错误 DOI 撞库 PDF | `2018_Li_Edge_...pdf`（边云协同预印本，已在 bib 为 `li2018edge`） |

**附录 NR-IQA**：主文引 `mittal2012niqe`（NIQE）；本地 BRISQUE 预印本仅作 **方法背景**，不等同 NIQE 原文。

**bib 核对提示**：`kang2017neurosurgeon` 的 DOI 在 OpenAlex 中常见为 `...3037698`，稿内为 `...3037728`，投稿前建议在 ACM Digital Library 核对一次。

---

## 二、本目录 18 个 PDF 的分类

| 类别 | 数量 | 说明 |
|------|------|------|
| **A. RA-L 正文已引且有 PDF** | **6** | 见第一节表 ✅ |
| **B. `references.bib` 补充 OA（20 页稿/方法背景）** | 3 | `li2018edge`、BRISQUE 预印本、Qibo TCM LLM |
| **C. 延伸阅读（未在 RA-L 正文 `\cite`）** | 9 | MUSIQ、TOPIQ、Toolformer 等 |
| **D. 已移除** | 1 | ~~`2023_Kalana_GPT-4_...`~~（错误文献，已删） |

### B. 2026-06-04 新下载（scholar-search）

| 文件名 | cite / 用途 | 来源 |
|--------|-------------|------|
| `2022_Macenski_Robot_Operating_System_2_...pdf` | `moore2021ros2` | arXiv:2204.09222 |
| `2018_Li_Edge_Intelligence_On-Demand_...pdf` | `li2018edge`（bib 已有） | arXiv:1806.07840 |
| `2012_Mittal_No-Reference_Image_Quality_...pdf` | NIQE 背景 / BRISQUE | arXiv:1206.4210 |
| `2024_Zhang_Qibo_A_Large_Language_Model_...pdf` | TCM 补充背景 | arXiv:2403.16056 |

### C. 本地有 PDF、但 RA-L 7 页稿未引用（研究背景用）

| 文件名 | 对应 bib（若有） | 备注 |
|--------|------------------|------|
| `2021_Ke_MUSIQ_...pdf` | `ke2021musiq` | 20 页稿 Related 可引；RA-L 已删节 |
| `2024_Chen_TOPIQ_...pdf` | `chen2024topiq` | 同上 |
| `2024_Chen_PromptIQA_...pdf` | — | 仅本地库 / 未写入 `references.bib` |
| `2022_Golestaneh_TReS_...pdf` | — | 仅本地库 |
| `2026_Fu_DRExperts_...pdf` | — | 仅本地库 |
| `2023_Schick_Toolformer_...pdf` | `schick2023toolformer` | 20 页稿引用 |
| `2024_Wang_A_survey_on_large_language_model_...pdf` | — | 仅本地库 |
| `2021_Xu_A_Survey_on_Edge_Intelligence.pdf` | — | 仅本地库 |
| `2026_Deng_OP4KSR_...pdf` | — | 辅助阅读，未入 bib |

### D. 已删除的错误 PDF

曾存在 `2023_Kalana_GPT-4_Technical_Report.pdf`（DOI 指向非 OpenAI 文档）。**已删除**；投稿稿未引用 GPT-4。若需 GPT-4 技术报告请单独下载 [arXiv:2303.08774](https://arxiv.org/abs/2303.08774)。

---

## 三、完整 `references.bib` 与本地库关系

- `latex/references.bib` 当前约 **40+** 条（含未在正文出现的条目、软件 misc 等）。
- `downloaded_refs.bib` 仅索引 **已下载的 15 篇** 延伸阅读 / 部分方法论文。
- **20 页 archive 稿**（`main.tex`）比 RA-L 稿引用更多（如 `schick2023toolformer`、`ke2021musiq`、`zhang2018blind` 等），其中部分在 `data/papers/` 有 PDF，详见 `cite_audit.json`。

---

## 四、真实性核验原则（投稿前）

1. **以 `references.bib` 为准**：题名、作者、年份、期刊、DOI 与 IEEE 引用格式一致；勿仅凭 PDF 文件名反推 bib。
2. **有本地 PDF 时**：核对 PDF 首页题名 / DOI 与 bib 一致（arXiv 预印本 DOI 常以 `10.48550/arXiv.xxx` 形式与正式会议 DOI 并存，以 bib 选用的为准并在表注说明）。
3. **无本地 PDF 时**：通过 DOI 链接在出版社或 Google Scholar 核对；**允许无 PDF**，不允许 bib 元数据虚构。
4. **禁止**：将未在 `references.bib` 登记的 PDF 写入 `\cite{}`；将 D 类错误 PDF 当作引文来源。
5. **定期审计**：

```bash
python3 doctor/paper1/scripts/paper1_audit_papers.py
# 输出 cite_audit.json

# 补下载合法 OA（仅开放获取）
python3 doctor/paper1/scripts/paper1_fetch_ral_missing_pdfs.py
python3 .agent/skills/scholar-search/scripts/download_papers.py \
  --input doctor/paper1/data/papers/ral_download_batch.json \
  --output-dir doctor/paper1/data/papers/
```

---

## 五、文件索引

| 文件 | 用途 |
|------|------|
| `*.pdf` | 本地全文（15 篇，约 65 MB） |
| `papers_index.json` | 下载时间、DOI、文件名映射 |
| `downloaded_refs.bib` | 已下载文献的 bib 片段 |
| `cite_audit.json` | RA-L 引用 ↔ PDF 自动对照 |
| `cite_key_map.json` | cite 键 → 文件名（含预印本说明） |
| `ral_download_batch.json` | scholar-search 下载批次输入 |
| `ral_missing_resolved.json` | 缺失引用的 OA 解析日志 |
| `README.md` | 本说明 |

---

## 六、延伸阅读文献详情（本地 PDF 逐篇说明）

> 下列为 **研究背景文库** 的逐篇摘要，**不等同**于「均已写入 RA-L 投稿正文」。  
> RA-L 正文引用状态见 **第一节**。

### 方向：无参考图像质量评估（NR-IQA）

#### 1. MUSIQ — `2021_Ke_MUSIQ_...pdf`（5.4 MB）

- **DOI**：`10.48550/arXiv.2108.05997` · [arXiv](https://arxiv.org/abs/2108.05997)
- **与稿关系**：20 页稿 Related；RA-L 正文未引。

#### 2. CLIP-IQA — `2023_Wang_Exploring_CLIP_...pdf`（22 MB）

- **DOI**：`10.1609/aaai.v37i2.25353`（bib 键 `wang2023clipiqa`）
- **与稿关系**：**RA-L 正文已引** ✅

#### 3. TOPIQ — `2024_Chen_TOPIQ_...pdf`（6.9 MB）

- **DOI**：`10.48550/arXiv.2308.03060`
- **与稿关系**：20 页稿；RA-L 未引。

#### 4. HyperIQA — `2020_Su_HyperIQA_...pdf`（2.3 MB）

- **DOI**：`10.1109/CVPR42600.2020.00372`（bib `su2020hyperiqa`）
- **与稿关系**：**RA-L 正文已引** ✅

#### 5. TReS — `2022_Golestaneh_TReS_...pdf`（286 KB）

- **DOI**：`10.48550/arXiv.2108.10951`
- **与稿关系**：仅本地库。

#### 6. PromptIQA — `2024_Chen_PromptIQA_...pdf`（3.2 MB）

- **DOI**：`10.48550/arXiv.2403.04993`
- **与稿关系**：仅本地库。

#### 7. DR.Experts — `2026_Fu_DRExperts_...pdf`（2.9 MB）

- **与稿关系**：仅本地库；预印本 / OpenAlex，**投稿 bib 未收录**。

### 方向：LLM 智能体

#### 8. ReAct — `2023_Yao_ReAct_...pdf`（619 KB）

- **DOI**：`10.48550/arXiv.2210.03629`（bib `yao2023react`）
- **与稿关系**：**RA-L 正文已引** ✅

#### 9. Toolformer — `2023_Schick_Toolformer_...pdf`（643 KB）

- **DOI**：`10.48550/arXiv.2302.04761`
- **与稿关系**：20 页稿；RA-L 未引。

#### 10. LLM Agent Survey — `2024_Wang_A_survey_...pdf`（4.2 MB）

- **DOI**：`10.1007/s11704-024-40231-1`
- **与稿关系**：仅本地库。

### 方向：边缘智能

#### 12. Zhou Edge Intelligence — `2019_Zhou_Edge_Intelligence_...pdf`（3.7 MB）

- **DOI**：`10.1109/JPROC.2019.2918951`（bib `zhou2019edge`）
- **与稿关系**：**RA-L 正文已引** ✅

#### 13. Xu Edge Intelligence Survey — `2021_Xu_A_Survey_on_Edge_Intelligence.pdf`（4.0 MB）

- **DOI**：`10.48550/arXiv.2003.12172`
- **与稿关系**：仅本地库。

#### 14. MobileNetV2 — `2018_Sandler_MobileNetV2_...pdf`（1.5 MB）

- **DOI**：`10.1109/CVPR.2018.00474`（bib `sandler2018mobilenetv2`）
- **与稿关系**：**RA-L 正文已引** ✅

### 辅助

#### 15. OP4KSR — `2026_Deng_OP4KSR_...pdf`（2.6 MB）

- **与稿关系**：仅本地库；未入 `references.bib`。

---

## 七、待办（可选）

| 优先级 | 动作 |
|--------|------|
| P0 | 投稿前用 DOI 逐条核对第一节中 6 条 **无 PDF** 的 RA-L 引用 |
| P1 | 核对 `kang2017neurosurgeon` DOI（3037728 vs 3037698）与 ACM 记录 |
| P2 | 机构订阅下手动下载 5 条无 OA 引文 PDF，并更新 `cite_key_map.json` |
| P2 | 改 bib 后运行 `paper1_audit_papers.py` |

---

> **维护**：更新 `references.bib` 或增删 PDF 后，请运行 `paper1_audit_papers.py` 并同步修订本节表格。
