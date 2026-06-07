# 速查与模板

> 完整流程见 [设计方案.md](设计方案.md)。配置见 [config.md](config.md)。

## 输出文件（12 个）

```
{PAPER1_ROOT}/reviews/{run_id}/
├── 00-上下文清单.md
├── 01-预检报告.md
├── 02-审稿人A-方法论.md
├── 02-审稿人B-领域.md
├── 02-统计审查.md
├── 02-编辑审查.md
├── 02-伦理审查.md
├── 03-交互质询纪要.md
├── 04-PI综合裁决.md
├── 05-全面评审报告.md      ★ 主交付物
├── 行动清单.md
└── 执行摘要.md             ★ 对话优先展示
```

## 预检 C1–C10 / T1–T10

见 [已知问题清单.md](已知问题清单.md)。当前 Paper I 使用 C1–C10 + T1–T10；角色勾选清单见 [审核细则.md](审核细则.md)。

## 引用归档 C3 / H5

```bash
PAPER1_ROOT=doctor/paper1
python3 "$PAPER1_ROOT/scripts/check_paper1_refs.py"
python3 "$PAPER1_ROOT/scripts/paper1_audit_papers.py"
```

审计要求见 [参考文献归档细则.md](参考文献归档细则.md)。`01-预检报告.md` 与 `05-全面评审报告.md` 需记录 `data/papers/cite_audit.json` 摘要。

## 投稿专检 T1–T10

RA-L / RCIM 投稿前检查见 [期刊投稿要点.md](期刊投稿要点.md)。若用户指定其他期刊，以用户目标为准并在 `00-上下文清单.md` 记录。

## 交互议题簇

| ID | 主题 |
|----|------|
| CL-RTT | M1/M2 与数值一致性 |
| CL-STRUCT | RA-L 篇幅与删节 |
| CL-IQA | Edge-IQA vs B3 |
| CL-CLINICAL | 数据集与临床外推 |
| CL-ROBOT | 机器人闭环贡献是否足够突出 |
| CL-REF | 引用归档、前沿覆盖与可审计性 |
| CL-REVISE | 重大修改方案、版本化 PDF 与二次评审闭环 |

## Major Issue 模板

```markdown
### METHOD-M1: 标题
- **位置**: `latex/sections/xx.tex` L10-L25
- **证据**: `experiments/results/table_ii.json` -> 字段路径
- **问题**: ...
- **建议**: ...
- **修改 sketch**: (diff 方向或改写示例)
- **验收标准**: (可自动化验证的条件)
- **需同步文件**: (修改此处后需同步的其他文件)
```

## 05-全面评审报告 目录

1. 元信息  2. 执行摘要  3. 预检  4. 分角色审稿  5. 交互质询
6. 综合问题清单（P0→P2）  7. 亮点  8. 修改路线图  9. 证据索引

## 行动清单模板

```markdown
| ID | 优先级 | 负责人 | 状态 | 关联 | 描述 | 位置 |
| AP-001 | P0 | 作者 | [ ] | C3 | … | `00_abstract.tex` |
```

## 重大修改闭环

当用户要求“按行动清单改稿/重大修改/二次评审”时，读取 [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md)，至少输出：

- `{PAPER1_ROOT}/docs/YYYYMMDD-HHMMSS-重大修改改进方案.md`
- 版本化 PDF：`{PAPER1_ROOT}/docs/v{N}-paper1-ral-YYYYMMDD-HHMMSS.pdf`（若成功编译）
- `{PAPER1_ROOT}/docs/YYYYMMDD-HHMMSS-二次评审报告.md`
- 更新后的 Point-by-Point Response 或 cover letter（用户需要时）

## 执行摘要模板

```markdown
# Paper I 审核执行摘要
- **决定**:
- **评分**: 审稿人 A / 审稿人 B
- **P0 共 n 项**:
- **最优先 3 件事**:
- **亮点**:
- **完整报告**: {PAPER1_ROOT}/reviews/{run_id}/05-全面评审报告.md
```

## 回归验证（多轮迭代）

改稿后再次审核时，参见 [回归验证.md](回归验证.md)。包含 P0 关闭验证模板、新问题检测清单、`diff-summary.md` 模板。

## 技能包内全部文档

[README.md](README.md) · [SKILL.md](SKILL.md) · [config.md](config.md) · [config.example.md](config.example.md) · [审核细则.md](审核细则.md) · [期刊投稿要点.md](期刊投稿要点.md) · [参考文献归档细则.md](参考文献归档细则.md) · [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) · [设计方案.md](设计方案.md) · [角色定义手册.md](角色定义手册.md) · [已知问题清单.md](已知问题清单.md) · [论文领域要点.md](论文领域要点.md) · [改稿衔接.md](改稿衔接.md) · [回归验证.md](回归验证.md)
