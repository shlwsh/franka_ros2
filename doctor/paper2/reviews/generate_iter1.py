import os
from datetime import datetime
import json

base_dir = "/home/ros/work/paper2/doctor/paper2/reviews/iter1"
os.makedirs(base_dir, exist_ok=True)

files = {}

files["00-上下文清单.md"] = """# Phase 0 上下文清单
- 论文目录：`doctor/paper2`
- 主稿文件：`latex/main.tex`, `latex/main-zh.tex` (Monolithic files, no `\\input` sections)
- 实验结果：`experiments/results/*.csv`
"""

files["01-预检报告.md"] = """# 01-预检报告
## 确认的问题
| ID | 严重性 | 文件:行 | 描述 | 证据 |
|----|------|------|------|------|
| C6 | 🔴 | `main.tex` | 缺少独立的 Discussion 章节，结论过短 | Monolithic 结论部分仅 1 段 |
| C7 | 🔴 | `main.tex` | 方法部分公式描述过于简略 | $\\gamma$ 参数缺乏具体解释 |

## 预检通过项
- C4: 参考文献已包含 DOI，格式规范。
"""

files["02-审稿人A-方法论.md"] = """[角色切换] 以下以 审稿人A（方法论）身份独立审稿，不参考其他角色的结论

## 总体决定
major_revision

## 评分（1-10）
| 维度 | 分数 |
|------|------|
| technicalNovelty | 7 |
| experimentalRigor | 6 |
| reproducibility | 8 |
| clarity | 5 |
| **overall** | 6.5 |

## Major Issues
### METHOD-M1: 方法描述不充分
- **位置**: `main.tex` Section 2
- **问题**: KG 门控公式 $\\gamma = 0.28 C_e + 0.24 Q_v + 0.36 K_c - 0.22 P_c$ 中的权重是如何确定的？缺乏依据。
- **建议**: 添加权重来源的解释或说明其为经验超参数。
- **修改 sketch**: 在公式后增加一句解释权重的来源。
- **验收标准**: 公式下文增加一段文字描述。

[角色退出] 审稿人A（方法论）审稿完成
"""

files["02-审稿人B-领域.md"] = """[角色切换] 以下以 审稿人B（领域）身份独立审稿，不参考其他角色的结论

## 总体决定
minor_revision

## Major Issues
### DOMAIN-D1: 临床意义缺失
- **位置**: `main.tex` Section 1 & 5
- **问题**: 虽然提到了合成与防幻觉，但在实际医疗场景中的应用前景讨论不够。
- **建议**: 在引言或结论中增加一段具体的临床使用场景（如远程多模态随访）。

[角色退出] 审稿人B（领域）审稿完成
"""

files["02-统计审查.md"] = """[角色切换] 以下以 统计审查 身份独立审稿

## Major Issues
### STAT-S1: 实验表格缺失置信区间
- **位置**: `main.tex` Table 1
- **问题**: F1 和 Halluc. 指标仅给出了单一点估计，缺乏标准差或 CI。
- **建议**: 由于是 MVP Draft，如果 24 个 trial 不足以计算 CI，需在文字中明确这是初步单次 run 结果。

[角色退出] 统计审查 审稿完成
"""

files["02-编辑审查.md"] = """[角色切换] 以下以 编辑审查 身份独立审稿

## Major Issues
### EDIT-E1: Abstract 篇幅
- **问题**: Abstract 对于一个系统架构的描述过长。
- **建议**: 精简摘要的系统成分列举。

[角色退出] 编辑审查 审稿完成
"""

files["02-伦理审查.md"] = """[角色切换] 以下以 伦理审查 身份独立审稿

## 通过: 否
### 违规项
- ETHICS-1: 缺乏明确的数据集隐私/IRB 声明。即使使用的是合成和去标识化数据，也应当在文中显式声明。
"""

files["03-交互质询纪要.md"] = """# 交互质询纪要
## 议题 1: 权重的解释 (METHOD-M1)
🔍 审稿人A：公式权重来源不明。
🔬 审稿人B：确实，需要交代。
📚 预检：代码中写死为常量。
**[共识]** 需要补充为经验超参数的声明。
"""

files["04-PI综合裁决.md"] = """# PI 综合裁决
**决定**: Major Revision
**总评**: 论文结构完整，基线清晰，但方法描述、临床意义和细节声明不足，需全面补充。
"""

files["05-全面评审报告.md"] = """# Paper 2 全面评审报告
## 0. 元信息
- run_id: iter1
- 时间: 2026-06-09
- 版本: v1.1.0

## 1. 综合建议
需解决公式解释、伦理声明、临床场景等问题。详情见行动清单。
"""

files["行动清单.md"] = """# Paper 2 修改行动清单
> run_id: iter1

## P0 - 必须先改
### AP-001: 补充超参数权重解释
- **来源**: METHOD-M1
- **状态**: [ ]
- **修改 sketch**: 在 Methods 中说明 0.28, 0.24 等为基于合成集的经验超参数。

### AP-002: 补充 IRB/伦理声明
- **来源**: ETHICS-1
- **状态**: [ ]
- **修改 sketch**: 在 Conclusion 或 Intro 明确本研究使用合成与去标识化数据，无需 IRB 审批。

## P1 - Major revision
### AP-003: 增加临床应用场景
- **来源**: DOMAIN-D1
- **状态**: [ ]
- **修改 sketch**: 在引言增加 "如远程多模态随访" 的举例。

### AP-004: 精简摘要与表格说明
- **来源**: EDIT-E1 / STAT-S1
- **状态**: [ ]
- **修改 sketch**: 简化 Abstract 的罗列；说明 Table 1 为初步运行结果无 CI。
"""

files["执行摘要.md"] = """# Paper 2 审核执行摘要
- **决定**: Major Revision
- **P0 共 2 项**: 补充超参数解释，补充伦理声明。
- **完整报告**: `doctor/paper2/reviews/iter1/05-全面评审报告.md`
"""

for k, v in files.items():
    with open(os.path.join(base_dir, k), "w", encoding="utf-8") as f:
        f.write(v)

print(f"Generated 12 files in {base_dir}")
