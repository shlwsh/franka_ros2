# 投稿包 RA-L_20260529

> **状态**：2026-06-04 · Minor Revision 改稿完成，待导师终审后上传  
> **审核报告**：`../../reviews/20260603-213904/`

## 打包命令

```bash
cd doctor/paper1/submission/RA-L_20260529
cp ../../latex/main.pdf ./manuscript.pdf
cp ../../latex/main-zh.pdf ./manuscript-zh.pdf   # 可选中文稿
cp ../../latex/references.bib ./
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `manuscript.pdf` | 英文稿（由 `latex/main.pdf` 复制） |
| `references.bib` | 参考文献（2026-06-03 已补 DOI） |
| `cover_letter.md` | Cover Letter 草稿（数字与 Table II 一致） |
| `graphical_abstract.md` | Graphical Abstract 布局与 caption |
| `credit_roles.md` | CRediT 作者贡献 |
| `log.md` | 投稿进度日志 |

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
- M1 基于 **simulated latency model**

## 投稿前检查

见同目录 `log.md` Checklist。
