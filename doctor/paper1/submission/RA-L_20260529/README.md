# 投稿包 RA-L_20260529

> **状态**：2026-06-04 · **RA-L 合规稿**（IEEEtran **7 页**，上限 8 页）已同步，待导师终审后上传  
> **审核报告**：`../../reviews/20260604-171256/`（投稿包终审）；上轮 `../../reviews/20260603-213904/`

## 打包命令

```bash
bash scripts/paper1_build_ral.sh
# 或手动：
cd doctor/paper1/latex && pdflatex main-ral.tex && bibtex main-ral && pdflatex main-ral.tex && pdflatex main-ral.tex
cp doctor/paper1/latex/main-ral.pdf doctor/paper1/submission/RA-L_20260529/manuscript.pdf
cp doctor/paper1/latex/references.bib doctor/paper1/submission/RA-L_20260529/
```

> **RA-L 页数**：正文 PDF **≤8 页**（含图表与参考文献）；附录内容见 `doctor/paper1/supplementary/SUPPLEMENTARY.md`，**不得写入 PDF**。  
> **完整技术稿**（20 页 archive）：`latex/main.pdf`，仅供内部参考，不上传系统。

## 文件清单

| 文件 | 说明 |
|------|------|
| `manuscript.pdf` | **RA-L 投稿稿**（IEEEtran，**7 页**，由 `latex/main-ral.pdf` 复制，2026-06-04） |
| `manuscript-zh.pdf` | 中文 archive 稿（16 页，内部归档，不上传） |
| `references.bib` | 参考文献（2026-06-04 同步） |
| `cover_letter.md` | Cover Letter 草稿（数字与 Table II 一致） |
| `graphical_abstract.png` | **Graphical Abstract 上传图**（1200×600，2026-06-04） |
| `graphical_abstract.md` | GA 布局说明与 caption |
| `credit_roles.md` | CRediT 作者贡献 |
| `log.md` | 投稿进度日志 |
| **中文 md 译本** | `../RA-L_20260529-zh/`（导师审阅用，系统上传仍以本目录英文稿为准） |

## 补充材料

| 内容 | 路径 |
|------|------|
| **在线补充材料（RA-L 合规）** | `../../supplementary/SUPPLEMENTARY.md` |
| 脱敏 JSONL 样例 | `docs-zh/paper1/V19/samples/run_001.sample.jsonl` |
| 在线 Walkthrough | `../../supplementary/online_walkthrough.md` |
| 复现说明 | `../../REPRODUCE.md` |
| 完整 20 页技术稿 | `../../latex/main.pdf`（archive，不上传） |

## 定稿数字速查（Table II，勿手改）

| 指标 | B0 | B2 |
|------|-----|-----|
| M1 p50 | 374.0 ms | **208.3 ms** |
| M2 | 0.560 | **0.604** |

- τ_B2 = 0.465；separation = −0.541  
- B3/B4 M2 ≈ 0.93（Table III，学习型对照）  
- M1 基于 **simulated latency model**

## 投稿前检查

见同目录 `log.md` Checklist。
