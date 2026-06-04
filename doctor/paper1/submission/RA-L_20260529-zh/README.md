# 投稿包 RA-L_20260529（中文版文档）

> **状态**：2026-06-04 · 英文投稿包已切换为 RA-L 合规 IEEEtran 稿（7 页）  
> **英文投稿包**：`../RA-L_20260529/`  
> **审核报告**：`../../reviews/20260603-213904/`

本目录为 `RA-L_20260529` 下 **Markdown 投稿辅助材料的中文译本**，供导师审阅与内部归档；**期刊系统上传仍以英文稿为准**（`../RA-L_20260529/manuscript.pdf` 等）。

## 打包命令

```bash
bash scripts/paper1_build_ral.sh
# PDF 仍从英文包或 latex 复制：
cp doctor/paper1/submission/RA-L_20260529/manuscript.pdf ./   # 若在本目录需要副本
```

中文版文档目录：

```bash
# 本目录仅含 md 译本，PDF 仍从英文包或 latex 复制
ls doctor/paper1/submission/RA-L_20260529-zh/
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `cover_letter.md` | 投稿信中文译稿（数字与 Table II 一致） |
| `graphical_abstract.md` | 图形摘要布局与图注中文译稿 |
| `credit_roles.md` | CRediT 作者贡献（中文说明） |
| `log.md` | 投稿进度日志（与英文包同步） |
| `README.md` | 本说明 |

英文包另含：`manuscript.pdf`、`references.bib`、`highlights.txt` 等，见 `../RA-L_20260529/README.md`。

## 补充材料

| 内容 | 路径 |
|------|------|
| 脱敏 JSONL 样例 | `docs-zh/paper1/V19/samples/run_001.sample.jsonl` |
| 在线 Walkthrough | `../../supplementary/online_walkthrough.md` |
| 复现说明 | `../../REPRODUCE.md` |

## 定稿数字速查（Table II，勿手改）

| 指标 | B0 | B2 |
|------|-----|-----|
| M1 p50 | 374.0 ms | **208.3 ms** |
| M2 | 0.560 | **0.604** |

- τ_B2 = 0.465；separation = −0.541  
- B3/B4 M2 ≈ 0.93（Table III，学习型对照）  
- M1 基于 **仿真延迟模型**

## 投稿前检查

见同目录 `log.md` 中的 Checklist。
