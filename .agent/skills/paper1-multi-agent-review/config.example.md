# 配置示例（复制到其他项目后重命名或合并为 config.md）

```markdown
| 变量 | 值 | 说明 |
|------|-----|------|
| PAPER1_ROOT | `path/to/your/paper` | LaTeX 根目录（含 latex/ 或等同结构） |
| 主稿英文 | `{PAPER1_ROOT}/latex/main.tex` | 若无 main.tex，改为实际主文件 |
| 投稿主稿 | `{PAPER1_ROOT}/latex/main-ral.tex` | 若无 RA-L 稿，改为目标期刊主文件 |
| 实验数据 | `{PAPER1_ROOT}/experiments/results/*.json` | 若无实验 JSON，Phase 1 改为人工证据表 |
| 引用归档 | `{PAPER1_ROOT}/data/papers/` | 可选；用于文献 PDF/快照审计 |
| 评审输出 | `{PAPER1_ROOT}/reviews/{run_id}/` | 自动创建 |
| TARGET_JOURNAL | `RAL` | 按目标改篇幅、格式和投稿材料标准 |
```

## 目录结构期望

技能默认假设 IMRaD LaTeX 结构：

- `{PAPER1_ROOT}/latex/main.tex` + `latex/sections/*.tex`
- 可选：`latex/main-zh.tex`、`latex/main-ral.tex`、`experiments/results/*.json`、`references.bib`、`submission/`、`data/papers/`

若结构不同，在 Phase 0 的 `00-上下文清单.md` 中**显式列出**实际主文件与章节目录。

## 可选：弱化 Paper I 专用预检

非 Paper I 项目可删除或忽略 [已知问题清单.md](已知问题清单.md) 中的 C1–C10 / T1–T10，在 Phase 1 改为用户提供的预检表，并同步改写 [审核细则.md](审核细则.md) 的角色问题。
