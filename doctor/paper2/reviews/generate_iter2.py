import os

base_dir = "/home/ros/work/paper2/doctor/paper2/reviews/iter2"
os.makedirs(base_dir, exist_ok=True)

files = {}

files["00-上下文清单.md"] = """# Phase 0 上下文清单
- 论文目录：`doctor/paper2`
- 当前版本：`v1.2.0 (Iter 1)`
- 检查上次的修改：公式解释已加入，伦理声明已加入。
"""

files["01-预检报告.md"] = """# 01-预检报告
## 预检通过项
- C6, C7: 结构与公式问题已初步修复。
- C4: 参考文献依旧正确。
"""

files["02-审稿人A-方法论.md"] = """[角色切换] 以下以 审稿人A（方法论）身份独立审稿

## 总体决定
minor_revision

## Major Issues
### METHOD-M2: GAT 基线描述不够细致
- **问题**: 在 Results 中提到了 graph-attention-lite 获得了 attention 权重，但并未明确说明这是在哪个层上取得的。
- **建议**: 指明是最后一层或特定机制的 attention。

[角色退出] 审稿人A（方法论）审稿完成
"""

files["02-审稿人B-领域.md"] = """[角色切换] 以下以 审稿人B（领域）身份独立审稿

## 总体决定
accept

## 优点
上一次建议的“远程多模态随访”场景补充得很到位。目前没有大的领域应用问题。

[角色退出] 审稿人B（领域）审稿完成
"""

files["02-统计审查.md"] = """[角色切换] 以下以 统计审查 身份独立审稿

## Minor Issues
### STAT-S2: 表格说明的语态
- **问题**: 虽然说明了没有置信区间，但建议用 "Since this is a preliminary single-run MVP, confidence intervals are omitted." 以更学术的语气表述。

[角色退出] 统计审查 审稿完成
"""

files["02-编辑审查.md"] = """[角色切换] 以下以 编辑审查 身份独立审稿

## Major Issues
### EDIT-E2: 中英文术语大小写不一致
- **问题**: 中文稿里 `synthetic MVP` 和 `graph-attention-lite` 有时混用，建议保持专有名词全大写首字母，如 `Synthetic MVP` 和 `Graph-Attention-Lite`。

[角色退出] 编辑审查 审稿完成
"""

files["02-伦理审查.md"] = """[角色切换] 以下以 伦理审查 身份独立审稿

## 通过: 是
- 上一轮加入的 IRB 豁免声明非常规范。
"""

files["03-交互质询纪要.md"] = """# 交互质询纪要
## 无明显分歧
各审稿人都认为第一轮修改大幅提升了论文质量。只需解决编辑审查的小问题和方法论补充说明即可。
"""

files["04-PI综合裁决.md"] = """# PI 综合裁决
**决定**: Minor Revision
**总评**: 论文状态已经非常接近 Submission-ready。只需执行最后一点术语规范化及细节打磨即可定稿。
"""

files["05-全面评审报告.md"] = """# Paper 2 全面评审报告
## 0. 元信息
- run_id: iter2
- 时间: 2026-06-09
- 版本: v1.2.0

## 1. 综合建议
进入最后的 polish 阶段。
"""

files["行动清单.md"] = """# Paper 2 修改行动清单
> run_id: iter2

## P1 - Minor revision
### AP-005: 补充 GAT 基线的注意力层说明
- **来源**: METHOD-M2
- **状态**: [ ]
- **修改 sketch**: 在 Results (结果) "The trainable graph-attention-lite run learns support attention..." 前加上 "In the final output layer, " (在最终输出层，)。

### AP-006: 学术语气及大小写规范
- **来源**: STAT-S2 / EDIT-E2
- **状态**: [ ]
- **修改 sketch**:
  - 表 1 caption 修改为更学术的语态 ("Since this is a preliminary single-run MVP, confidence intervals are omitted.")
  - 将 `synthetic MVP` 统一为 `Synthetic MVP`，`graph-attention-lite` 统一为 `Graph-Attention-Lite`。
"""

files["执行摘要.md"] = """# Paper 2 二轮审核执行摘要
- **决定**: Minor Revision
- **P1 共 2 项**: 补充网络层说明，规范化术语与大小写。
- **完整报告**: `doctor/paper2/reviews/iter2/05-全面评审报告.md`
"""

for k, v in files.items():
    with open(os.path.join(base_dir, k), "w", encoding="utf-8") as f:
        f.write(v)

print(f"Generated 12 files in {base_dir}")
