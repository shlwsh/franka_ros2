# 投稿日志 RA-L_20260529

> **更新**：2026-06-04（英文投稿包 PDF 已与 `latex/` 最新稿同步）  
> **英文投稿包**：`../RA-L_20260529/` · **中文 md 译本**：本目录

| 日期 | 动作 | 状态 |
|------|------|------|
| 2026-05-29 | AI 生成 Draft v1 `latex/main.pdf` | ✅ |
| 2026-05-31 | 全量主矩阵 3 seeds × 500 帧完成 | ✅ |
| 2026-06-03 | Minor Revision 改稿（P0–P2 共 12 项） | ✅ |
| 2026-06-03 | 多智能体审核 run `20260603-213904`，PI **7.2/10** | ✅ Minor Revision |
| 2026-06-04 | 学习手册 + `doctor/paper1` 文档同步 | ✅ |
| 2026-06-04 | 投稿包 md 中文译本 → `RA-L_20260529-zh/` | ✅ |
| 2026-06-04 | 英文包 RA-L 合规稿 `manuscript.pdf`（IEEEtran 7 页）同步 | ✅ |
| — | 导师终审 | ⏳ 待办 |
| — | 投稿系统创建 + 上传 | ⏳ 学生 |
| — | 通讯作者确认 | ⏳ 学生 |

## Checklist（2026-06-04）

- [x] Table II 与 `main_seed*.csv` / `table_ii.json` 一致
- [x] Abstract / Cover Letter 定量句与 CSV 一致
- [x] bootstrap CI 写入 Table II 表注
- [x] Fig.3 负分离度（−0.541）主文可视化
- [x] Fig.4/5 caption 标明 simulated latency
- [x] 分层 M2、Pareto、NR-IQA 附录
- [x] Walkthrough 移出正文 → `supplementary/online_walkthrough.md`
- [x] `references.bib` DOI 补全
- [x] 辅轨 M6 未写入主结论
- [x] 补充材料无患者原图
- [x] 投稿 md 中文译本（本目录）
- [x] 编译 PDF 确认 RA-L 页数预算（IEEEtran **7 页**，上限 8 页）
- [ ] DCO / 作者单位 / 基金致谢终检
- [ ] 查重与英文润色（学生终稿）

## 改稿对照（20260603-213904 行动清单）

| ID | 项 | 状态 |
|----|-----|------|
| AP-001 | 负分离度主文可视化 | ✅ |
| AP-002 | Discussion 合并为连贯段落 | ✅ |
| AP-003 | references.bib DOI | ✅ |
| AP-004 | Fig.4/5 simulated RTT 图注 | ✅ |
| AP-005 | NR-IQA 附录 | ✅ |
| AP-006 | bootstrap CI | ✅ |
| AP-007 | Pareto Fig.6 | ✅ |
| AP-008 | Walkthrough → supplementary | ✅ |
| AP-009 | 分层 M2 | ✅ |
| AP-010 | 失败模式示意 Fig.8 | ✅ |
| AP-011 | Graphical Abstract 草稿 | ✅ |
| AP-012 | 中文附录结构同步 | ✅ |

## 文件清单

**英文投稿包（`../RA-L_20260529/`）**

- `../../latex/main.pdf`、`../../latex/main-zh.pdf`
- `../../latex/references.bib`
- `cover_letter.md`（英文）
- `graphical_abstract.md`（英文）
- `credit_roles.md`
- `highlights.txt`
- `../../../docs-zh/paper1/V19/samples/run_001.sample.jsonl`
- `../../supplementary/online_walkthrough.md`
- `../../reviews/20260603-213904/执行摘要.md`

**中文 md 译本（本目录）**

- `cover_letter.md`
- `graphical_abstract.md`
- `credit_roles.md`
- `log.md`
- `README.md`
