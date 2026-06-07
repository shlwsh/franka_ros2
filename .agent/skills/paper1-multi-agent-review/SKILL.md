---
name: paper1-multi-agent-review
description: >-
  Simulates multi-role peer review of Paper I at doctor/paper1 or a user-specified
  LaTeX manuscript: context precheck, blind role review, cross-examination, PI
  synthesis, regression review, and major-revision closure. Writes reports under
  {PAPER1_ROOT}/reviews/{run_id}/. Use when the user asks to review Paper I,
  run multi-agent paper review, 执行 Paper I 多角色审核, 投稿前审核, RA-L/RCIM
  审稿模拟, RA-L 6-page readiness check, double-anonymous compliance,
  回归验证, 重大修改闭环, or simulate peer reviewers.
disable-model-invocation: false
---

# Paper I 多智能体交互式论文审核

**本技能包自包含**：执行前阅读 [config.md](config.md)；**各角色勾选清单**见 [审核细则.md](审核细则.md)。
**目标期刊模式**：默认 RA-L / RCIM；投稿前要求见 [期刊投稿要点.md](期刊投稿要点.md)，官网最新规则由作者最终确认。
**RA-L 专审**：默认执行 6 页目标、最多 8 页上限、双匿名、PaperCept、R&R 30 天、多媒体/视频、AI/COI/Data availability 门禁，并检查示范 RA-L 论文对照与引用覆盖（建议 20--40 条；6 页短稿低于 15 条视为 P1 风险）。

## 启动时必读（按序）

1. [config.md](config.md) — 路径、`TARGET_JOURNAL`、主稿与实验数据出口
2. [审核细则.md](审核细则.md) — Phase 1–2 各角色高效勾选清单
3. [已知问题清单.md](已知问题清单.md) — Paper I 预检 C1–C10 + T1–T10
4. [参考文献归档细则.md](参考文献归档细则.md) — 引用核实与 `data/papers/` 归档
5. [期刊投稿要点.md](期刊投稿要点.md) — RA-L / RCIM 投稿前检查
6. [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) — 基准论文对照、引用密度、重大修改、二次评审
7. [论文领域要点.md](论文领域要点.md) — SQ、基线、机器人舌象/IQA 上下文
8. [角色定义手册.md](角色定义手册.md) — 扮演语气与职责

## 使用时机

- **执行 Paper I 多角色审核** / **投稿前审核** / **模拟审稿人** / **全面评审建议**
- 投稿前要 P0/P1/P2 行动清单与落盘报告
- 对照 RA-L/RCIM 口径、基准论文或上一轮行动清单做重大修改闭环
- 根据评审意见生成 `docs/YYYYMMDD-HHMMSS-*.md` 方案、修改主稿、编译版本化 PDF、二次评审
- **默认不改 `.tex`**（改稿见 [改稿衔接.md](改稿衔接.md)）

## 路径（来自 config.md）

| 项 | 默认 |
|----|------|
| `PAPER1_ROOT` | `doctor/paper1` |
| 主稿英文 | `{PAPER1_ROOT}/latex/main.tex`、`main-ral.tex` |
| 主稿中文 | `{PAPER1_ROOT}/latex/main-zh.tex` |
| 实验真相 | `{PAPER1_ROOT}/experiments/results/*.json` |
| 引用归档 | `{PAPER1_ROOT}/data/papers/` |
| 输出 | `{PAPER1_ROOT}/reviews/{run_id}/` |
| `run_id` | `YYYYMMDD-HHmmss` |

用户指定其他论文目录时，覆盖 `PAPER1_ROOT`。

## 执行承诺

1. 完成 Phase 0→5，落盘 **12 个文件**（见 [reference.md](reference.md)）
2. 盲审互不可见；Phase 3 后再交叉引用
3. Major 问题含 `tex` 路径、实验 JSON 字段、编译日志或引用审计证据
4. 数值以仓库 JSON/CSV 为准，禁止编造
5. 对话末尾贴执行摘要 + 主报告路径
6. 中文撰写（引文可英文）

## 任务清单

```text
Phase 0  🎯 → 00-上下文清单.md
Phase 1  📚 → 01-预检报告.md        （C1–C10 + T1–T10；跑可用审计脚本）
Phase 2  🔍 → 02-审稿人A-方法论.md  （按 审核细则 §2）
Phase 2  🔬 → 02-审稿人B-领域.md    （按 审核细则 §3）
Phase 2  📊 → 02-统计审查.md        （按 审核细则 §4）
Phase 2  ✍️ → 02-编辑审查.md        （按 审核细则 §5）
Phase 2  📐 → 02-伦理审查.md        （按 审核细则 §6）
Phase 3      → 03-交互质询纪要.md   （议题簇见 审核细则 §7）
Phase 4  🎓 → 04-PI综合裁决.md + 行动清单.md
Phase 5  🎯 → 05-全面评审报告.md + 执行摘要.md
```

## 分阶段要点

**Phase 0**：读 `main.tex` / `main-ral.tex` / `main-zh.tex` 列 `\input`；统计 `sections/*.tex` 行数；列 `experiments/results/*.json` 与 `data/papers/*audit*.json`；写 `00-上下文清单.md`。

**Phase 1**：按 [审核细则.md §1](审核细则.md) 验证 C1–C10 / T1–T10；优先运行 `doctor/paper1/scripts/check_paper1_refs.py`、`doctor/paper1/scripts/paper1_audit_papers.py` 和可用构建脚本；输出 `确认的问题` / `待作者确认` / `预检通过项`。

**Phase 2**：五角色**按审核细则勾选**，勿重复通读全文；Issue 前缀 `METHOD-` `DOMAIN-` `STAT-` `EDIT-` `ETHICS-`。新增重点：算法形式化/伪代码、三贡献贯穿、2023+ IQA/机器人/边缘前沿覆盖、引用数量与质量、图文数据一致、误差条/置信区间、RA-L 篇幅与 IEEE 格式。

**Phase 3**：Top-3 分歧（CL-RTT / CL-STRUCT / CL-IQA / CL-CLINICAL / CL-REF 等）；对话体；`[共识]` / `[交 PI 裁决]`。

**Phase 4**：PI 决定 + P0≤7 的 `行动清单.md`（含验收标准、需同步文件）。

**Phase 5**：合并 [设计方案.md §5.7](设计方案.md) 目录结构 → `05-全面评审报告.md`。

## DoD

- [ ] `{PAPER1_ROOT}/reviews/{run_id}/` 下 12 文件齐全
- [ ] `05` 含综合问题清单，P0≤7
- [ ] ≥80% Major 有证据；已核对 `table_ii.json` / `table_ii*.json` vs Abstract
- [ ] C1–C10 / T1–T10 均有验证状态
- [ ] 引用审计脚本已运行或明确记录未运行原因
- [ ] 算法形式化、基线公平性、图文一致性、版本化改稿闭环已评估
- [ ] 对话已交付执行摘要

## 快捷命令

```bash
PAPER1_ROOT=doctor/paper1
find "$PAPER1_ROOT/experiments/results" -maxdepth 1 -name '*.json' -print | sort
grep -c '\\paragraph' "$PAPER1_ROOT/latex/sections/05_5_discussion.tex"
grep -Ei 'faq|reviewer faq' "$PAPER1_ROOT/latex/sections/" 2>/dev/null || true
grep -c '\\input{sections/05' "$PAPER1_ROOT/latex/main.tex"
python3 "$PAPER1_ROOT/scripts/check_paper1_refs.py"
python3 "$PAPER1_ROOT/scripts/paper1_audit_papers.py"
```

## 技能包文档索引

| 文件 | 用途 |
|------|------|
| [审核细则.md](审核细则.md) | **各角色高效勾选清单** |
| [参考文献归档细则.md](参考文献归档细则.md) | **引用核实与 papers/ 归档** |
| [期刊投稿要点.md](期刊投稿要点.md) | **RA-L / RCIM 投稿前检查** |
| [基准论文对照与改稿闭环.md](基准论文对照与改稿闭环.md) | **基准论文对照、重大修改闭环、二次评审** |
| [README.md](README.md) | 复制到其他项目 |
| [设计方案.md](设计方案.md) | 完整 Phase 细则 |
| [reference.md](reference.md) | 模板速查 |
| [改稿衔接.md](改稿衔接.md) | 审核后改稿 |
