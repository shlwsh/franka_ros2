# 06 · KG 门控与 GNN 基线详解

> **目标**：说清楚 KG 门控**怎么实现**、三种图基线**各做什么**、与业界 KG+LLM 路线**如何定位**（非宣称全面碾压）。

---

## 1. KG 门控实现逐步拆解

### 1.1 代码位置与调用链

| 层级 | 文件 | 作用 |
|------|------|------|
| KG 数据 | `doctor/paper2/kg/kg_stub.json` | 10 实体、7 支持边、4 矛盾边 |
| 边表导出 | `doctor/paper2/kg/export_edges.py` | JSON → `kg_edges.csv` |
| 门控核心 | `doctor/paper2/agents/kg_conflict_agent.py` | `compute_conflict_gate()` |
| 实体映射 | `doctor/paper2/kg/entity_map.csv` | FHIR/ICD/SNOMED placeholder |
| 路由消费 | `doctor/paper2/langgraph_router/routing.py` | `decide_route()` |
| 传播消融 | `doctor/paper2/experiments/run_kg_propagation.py` | signed-edge propagation |
| 嵌入消融 | `doctor/paper2/experiments/run_graph_embedding.py` | message-passing embedding |
| GAT-lite | `doctor/paper2/experiments/run_graph_attention.py` | 可训练注意力权重 |

**在线调用链**：

```
run_trial()
  → extract_symptom_entities()
  → evaluate_synthetic_vision()
  → compute_conflict_gate()
        → entity_completeness()
        → score_kg_consistency()  ← 读取 kg_stub.json
        → 加权求和 γ_conflict
  → decide_route(gate, baseline)
```

### 1.2 KG Stub 结构

`kg_stub.json` 包含三类信息：

| 字段 | 示例 | 含义 |
|------|------|------|
| `entities` | `fever`, `red_tongue`, ... | 10 个症状/体征实体 |
| `supports` | `[fever, red_tongue, 0.82]` | 文本-视觉支持关系 |
| `contradicts` | `[fever, pale_tongue, 0.55]` | 文本-视觉矛盾关系 |

**设计意图**：用中医舌诊场景的**小规则图**验证门控逻辑，而非替代 SNOMED/UMLS 大图谱。

### 1.3 门控算法流程

```
输入：symptom_entities, vision_tags, q_img, expected_entities
  │
  ▼
① 实体完整度 C_entity
     missing = expected − extracted
     C_entity = 1 − |missing| / |expected|
  │
  ▼
② 视觉质量 Q_vision = clip(q_img, 0, 1)
  │
  ▼
③ KG 一致性 C_kg
     遍历 supports：text ∩ vision 命中 → support = max(weight)
     遍历 contradicts：text ∩ vision 命中 → contradiction = max(weight)
     若无匹配：C_kg = 0.35（中性先验）
     否则：C_kg = clip(support − contradiction + 0.45, 0, 1)
  │
  ▼
④ 矛盾惩罚 P_contradict = contradiction（0 或边权重）
  │
  ▼
⑤ 融合：γ = 0.28·C_entity + 0.24·Q_vision + 0.36·C_kg − 0.22·P_contradict
  │
  ▼
输出：{ gamma_conflict, kg_matches, entity_completeness, ... }
```

### 1.4 伪代码（与论文一致）

```python
def compute_conflict_gate(symptom_entities, vision_tags, q_img, expected_entities, tau=0.65):
    completeness, missing = entity_completeness(symptom_entities, expected_entities)
    kg_consistency, contradiction, matches = score_kg_consistency(symptom_entities, vision_tags)
    gamma = (
        0.28 * completeness
        + 0.24 * q_img
        + 0.36 * kg_consistency
        - 0.22 * contradiction
    )
    return clip(gamma, 0, 1), matches, missing
```

### 1.5 权重设计 rationale

| 权重 | 分量 | 理由 |
|------|------|------|
| **0.36** | KG 一致性 | 论文 II 核心：语义冲突检测依赖 KG 证据 |
| **0.28** | 实体完整度 | 文本信息不足时应补问而非生成 |
| **0.24** | 视觉质量 | 继承论文 I 的 q_img 信号 |
| **0.22** | 矛盾惩罚 | 显式惩罚 text-vision 冲突边 |

> MVP 权重为手工设定；真实数据上应通过验证集网格搜索或学习权重重新标定。

---

## 2. 三种图基线消融

### 2.1 Signed-Edge Propagation（规则传播）

| 项 | 内容 |
|----|------|
| 脚本 | `experiments/run_kg_propagation.py` |
| 方法 | 从种子实体沿 supports/contradicts 边传播符号置信度 |
| 结果 | 24 trial 上 P/R/F1 = **1.0000** |
| 图表 | `figures/paper2_kg_propagation_scores.svg` |
| 局限 | stub 规模小，规则与门控等价 |

### 2.2 Message-Passing Embedding

| 项 | 内容 |
|----|------|
| 脚本 | `experiments/run_graph_embedding.py` |
| 方法 | KG 节点 one-hot 初始化 → 有符号消息传递 → 与文本/视觉池化向量余弦相似度 |
| 结果 | F1 = **1.0000** |
| 图表 | `figures/paper2_graph_embedding_scores.svg` |
| 局限 | 无外部 GNN 库；非大规模训练 |

### 2.3 Graph-Attention-Lite（可训练）

| 项 | 内容 |
|----|------|
| 脚本 | `experiments/run_graph_attention.py` |
| 方法 | 从 KG 边和 replay 标签学习 support/contradiction/low-quality 注意力 |
| 学习权重 | support = **-7.80**，contradiction = **6.18**，low-quality = **14.96** |
| 结果 | F1 = **1.0000** |
| 图表 | `figures/paper2_graph_attention_scores.svg` |
| 局限 | 小型线性模型；**不等价**于 PyG/DGL 上的 GAT |

### 2.4 三基线对比表

| 维度 | 规则门控 | 传播 | 嵌入 | GAT-lite |
|------|----------|------|------|----------|
| 可解释性 | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐ |
| 可训练 | ❌ | ❌ | ❌ | ✅（小） |
| 外部依赖 | 无 | 无 | 无 | 无 |
| MVP F1 | 1.00 | 1.00 | 1.00 | 1.00 |
| 适用阶段 | **当前主方法** | 消融对照 | 消融对照 | 后续扩展探针 |

> **关键论点**：三种图基线与规则门控在 stub 上**无法区分**——这恰恰说明需要接入真实大图谱才能评估 GNN 增益。

### 2.5 大图 GNN/GAT 证据审计

| 项 | 内容 |
|----|------|
| 脚本 | `experiments/run_large_gnn_evidence_audit.py` |
| 模板 | `experiments/configs/large_gnn_evidence.template.csv` |
| 审计输出 | `experiments/results/large_gnn_evidence_audit.csv` |
| 当前状态 | blocked：缺少真实 `large_gnn_evidence.csv` |

审计器不会训练模型，也不会把 GAT-lite 当作大图实验。它只接受满足以下条件的外部证据：

- licensed/approved 的图谱来源和本体标识状态
- 非 `synthetic/stub/placeholder-only/toy/fixture` 的图源描述
- 节点数和边数达到大图阈值，且边数不少于节点数
- 模型族属于 GNN/GAT/GCN/GraphSAGE 等图神经网络
- 训练、验证、测试划分均存在，seed 数大于 0
- 指标值、baseline 值、evidence URI、artifact SHA-256 可审计

因此 readiness 中的 `large_gnn_gat_experiment` 不再只是检查文件是否存在，而是要求这份审计通过。

---

## 3. 实体映射与许可证治理

### 3.1 entity_map.csv

| 列 | 说明 |
|----|------|
| `local_code` | 项目内实体名（如 `red_tongue`） |
| `fhir_target` | FHIR Coding 占位 |
| `icd10_placeholder` | ICD-10 占位（非真实码） |
| `snomed_placeholder` | SNOMED 占位（非真实码） |
| `license_status` | `placeholder-only` |

覆盖率：10/10 实体有映射（`entity_map_coverage.csv`）。

### 3.2 许可证约束

- `kg/ONTOLOGY_LICENSE_NOTES.md` 记录 SNOMED/UMLS 替换前约束
- 仓库**不分发**受限本体原文
- `run_ontology_identifier_audit.py` 生成 `kg/licensed_ontology_identifiers.template.csv`
- readiness audit 中 `licensed_ontology_identifiers` gate = **blocked**

### 3.3 授权标识证据审计

`run_ontology_identifier_audit.py` 不下载、不提交 ICD/SNOMED/UMLS 原文，只审计未来填入的授权映射证据。通过条件：

- 10/10 KG 实体均有 evidence row
- `icd_identifier` 或 `snomed_identifier` 至少一个非空，且不是 placeholder/stub/todo
- `license_status` 显示 licensed/approved/authorized/credentialed
- `approval_evidence_uri`、`source_release`、`source_artifact_sha256` 可追溯
- `restricted_text_in_repo=false`

当前默认离线运行只生成 template 和 blocked audit；这能防止把 `entity_map.csv` 的 project-local placeholder 当作授权本体实验。

---

## 4. 与业界 KG+LLM 路线对比

### 4.1 业界常见路线

| 路线 | 代表思路 | 优点 | 缺点 |
|------|----------|------|------|
| **RAG + LLM** | 检索 KG 片段注入 prompt | 实现简单 | 检索噪声、无冲突门控 |
| **KG 约束解码** | 生成时限制 token 空间 | 结构化 | 难处理多模态 |
| **Agent + Tool** | ReAct/Tool-calling | 灵活 | 幻觉路径难审计 |
| **本文：KG 门控状态机** | γ 低于阈值 → 不生成 | 可审计 JSONL | 需定制路由逻辑 |

### 4.2 本文定位句（答辩用）

> 我们不是用 KG 做 RAG 增强生成，而是用 KG **门控生成时机**——证据不足或模态冲突时，状态机**拒绝**进入 EMR 生成节点，转而触发具身/认知工具。这与「先生成再校验」的 self-reflection（B1）有本质区别。

### 4.3 与论文 I Edge-IQA 的类比

| 论文 I | 论文 II |
|--------|---------|
| Q_img 门控图像上行 | γ_conflict 门控 EMR 生成 |
| τ = 0.505（IQA 阈值） | τ_gating = 0.65（冲突阈值） |
| blur → resample | contradiction → query_kg |
| 可解释 flags | 可解释 kg_matches |

---

## 5. 优势论证（在 MVP 范围内）

### 5.1 相对 B0（线性生成）

- 冲突 F1：0.75 → **1.00**
- 幻觉率：0.625 → **0.00**（B2）
- 每个拦截决策有 `kg_matches` 证据

### 5.2 相对 B1（自反思）

- B1 无 KG → 幻觉率 **0.25**
- B2 有 KG → 幻觉率 **0.00**
- 证明：**浅层自反思不足以阻断语义冲突**

### 5.3 当前不能声称的优势

- ❌ 优于大规模 GNN（未训练）
- ❌ 优于真实 RAG 系统（未对比）
- ❌ 临床级 KG 覆盖（stub 仅 10 实体）
- ❌ 跨机构泛化（synthetic only）

---

## 6. 导师/审稿人可能追问

### Q：为什么不直接用 GraphRAG？

**答**：GraphRAG 解决「检索增强」，不解决「何时禁止生成」。本文门控是**硬阻断**——γ < τ 时不进入 EMR 节点，比 prompt 注入更可控、更可 JSONL 审计。

### Q：GAT-lite 权重说明什么？

**答**：low-quality attention（14.96）最高，说明在 synthetic 标签下**图像质量**对冲突预测贡献最大；support 为负可能是 stub 规模下的过拟合。**不能**外推为临床结论。

### Q：下一步 KG 怎么扩展？

**答**：① 获得 SNOMED/ICD 授权后替换 placeholder；② 从 MIMIC-IV-Note 派生实体；③ 在真实边上训练 GAT；④ 重新跑 B0–B4 主矩阵。

---

**下一篇** → [07_多Agent状态机与FHIR标准深度分析.md](./07_多Agent状态机与FHIR标准深度分析.md)
