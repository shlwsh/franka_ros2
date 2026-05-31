# 07 · 多 Agent 状态机与 FHIR 标准深度分析

> **文档版本**：V1 | 2026-05-31  
> **依据**：`doctor/paper2/langgraph_router/graph.py`、`agents/`、`tools/fhir_validator.py`  
> **目标读者**：论文 II 架构论证、导师技术审查、FHIR 互操作问答

---

## 1. 核心问题

论文 II 使用**多 Agent 状态图**组织 EMR 合成流程。两个自然问题是：

> 1. 为什么不直接用一次 LLM 调用 + prompt？
> 2. FHIR 校验在 MVP 中到底做了什么？

本章从**架构能力**和**标准合规**两个维度给出完整答案。

---

## 2. 多 Agent 状态机 vs 线性 LLM

### 2.1 五种候选方案

| # | 方案 | 类别 | MVP 对应 |
|---|------|------|----------|
| 1 | One-Shot LLM | 单次生成 | **B0** |
| 2 | Self-Reflection | 生成→反思→再生成 | **B1** |
| 3 | ReAct / Tool-Calling | 自由工具链 | （未单独基线） |
| 4 | **KG-Gated StateGraph（本文）** | **条件路由状态机** | **B2–B4** |
| 5 | Human-in-the-Loop Only | 全人工 | `human_review` 节点 |

### 2.2 实测对比（synthetic MVP）

| 方案 | F1 | Hallucination | FHIR Valid | 可审计性 |
|------|-----|---------------|------------|----------|
| B0 One-Shot | 0.75 | 0.625 | 0.75 | ❌ 无中间态 |
| B1 Self-Reflection | 1.00 | 0.25 | 0.50 | ⚠️ 浅层 |
| B2 KG-Gated | 1.00 | **0.00** | 0.25 | ✅ JSONL |
| B4 Tool-Enhanced | 1.00 | 0.25 | **0.625** | ✅ JSONL + tool_calls |

**关键解读**：

- B0 证明「一次生成」在冲突场景下**不可接受**（幻觉 62.5%）
- B1 证明「自反思」**不够**——无 KG 时仍有 25% 幻觉
- B2 证明 **KG 硬门控**可消除幻觉，代价是 FHIR 生成率下降
- B4 证明 **工具链**（补拍 + FHIR 修复）可部分恢复 FHIR 有效率

### 2.3 为什么状态图优于自由 Tool-Calling？

| 能力 | 自由 Tool-Calling | 本文 StateGraph |
|------|-------------------|-----------------|
| 路由可预测 | ❌ LLM 决定调用顺序 | ✅ `decide_route()` 确定性 |
| 证据链 | ⚠️ 依赖 LLM 日志 | ✅ Paper2State + JSONL |
| 基线对比 | 难复现 | B0–B4 可控消融 |
| 医疗审计 | 难通过 | 每步有 timestamp + tool_call |
| 与论文 I 一致 | 新框架 | 同一 LangGraph 范式 |

---

## 3. 状态图拓扑

### 3.1 节点与边（MVP 实现）

```
                    ┌─────────────┐
                    │ case input  │
                    └──────┬──────┘
                           ▼
              ┌────────────────────────┐
              │ symptom + vision + kg  │
              │   compute_conflict_gate │
              └────────────┬───────────┘
                           ▼
              ┌────────────────────────┐
              │     decide_route       │
              └────────────┬───────────┘
         ┌─────────┬───────┼───────┬─────────┐
         ▼         ▼       ▼       ▼         ▼
   resample   ask_     query_   generate   human_
   _vision   followup   _kg       _emr     review
         │         │       │       │         │
         └────┬────┘       │       ▼         │
              │            │   validate     │
              │            │   _fhir        │
              │            │       │        │
              │            │       ▼        │
              │            │   repair_fhir  │
              │            │   (B4 only)    │
              └────────────┴───────┴────────┘
                           ▼
                    JSONL write
```

### 3.2 各基线路径差异

| 路由决策 | B0 | B1 | B2 | B3 | B4 |
|----------|----|----|----|----|-----|
| generate_emr | 总是 | 条件允许 | γ≥τ | γ≥τ | γ≥τ |
| resample_vision | ❌ | ✅ | ❌ | ✅ | ✅ |
| ask_followup | ❌ | ✅ | ✅ | ✅ | ✅→human |
| query_kg | ❌ | ❌ | ✅ | ✅ | ✅ |
| repair_fhir | ❌ | ❌ | ❌ | ❌ | ✅ |
| human_review | ❌ | ❌ | ✅低质 | 部分 | ✅补问后 |

### 3.3 代码锚点

```python
# routing.py — 路由核心逻辑
def decide_route(gate, baseline, retry_count, max_retries=1):
    if baseline == "B0":
        return "generate_emr"
    if gate["entity_completeness"] < 1.0:
        return "ask_followup"
    if gate["vision_quality"] < 0.55:
        return "resample_vision" if baseline in ("B3", "B4") else "human_review"
    if gate["gamma_conflict"] >= gate["tau_gating"]:
        return "generate_emr"
    return "query_kg"
```

---

## 4. 五个 Agent 协作模式

### 4.1 Agent 职责矩阵

| Agent | 感知 | 认知 | 行动 | 生成 |
|-------|------|------|------|------|
| Symptom | ✅ 文本 | | | |
| Vision | ✅ 图像 | | | |
| KG Conflict | | ✅ 门控 | | |
| Action | | | ✅ 工具 | |
| EMR/FHIR | | | | ✅ 结构化 |

### 4.2 与 AutoGen/CrewAI 的区别

- AutoGen/CrewAI 是**对话编排**框架，Agent 间通过消息传递
- 本文 Agent 通过**共享 Paper2State** 传递，路由由**确定性函数**决定
- 优势：基线可控、JSONL 可复现；劣势：灵活性低于自由对话

### 4.3 与论文 I LangGraph 的继承

| 维度 | 论文 I | 论文 II |
|------|--------|---------|
| 状态对象 | q_img, retry_count | Paper2State（20+ 字段） |
| Agent 数 | 1（路由） | 5（分工） |
| 工具 | go_to_tongue_pose | + ask_followup, query_kg, repair_fhir |
| 图框架 | LangGraph 范式 | 同范式扩展 |

> 注：MVP 实现为**纯 Python 状态机**（`graph.py::run_trial`），与 LangGraph 库**概念对齐**但尚未引入 LangGraph 依赖。后续可迁移为正式 `StateGraph` 以获 checkpoint 能力。

---

## 5. FHIR 标准深度分析

### 5.1 MVP 生成的 Bundle 结构

```json
{
  "resourceType": "Bundle",
  "type": "document",
  "entry": [
    { "resource": { "resourceType": "Composition", ... } },  // 必须第一项
    { "resource": { "resourceType": "Patient", ... } },
    { "resource": { "resourceType": "Observation", ... } }  // 可 omit（测试用）
  ]
}
```

### 5.2 HL7 FHIR R4 关键约束

| 约束 | 来源 | MVP 实现 |
|------|------|----------|
| Bundle.type = `document` | FHIR R4 Bundle | ✅ |
| 首 entry 为 Composition | Document Bundle 规范 | ✅ 校验 |
| Composition.subject → Patient | Composition 资源 | ✅ |
| Observation.subject → Patient | Observation 资源 | ✅ |
| 互操作编码 | LOINC/SNOMED | ⚠️ text-only 占位 |

### 5.3 本地结构校验规则

`validate_fhir_bundle()` 检查：

1. `resourceType == "Bundle"`
2. `type == "document"`
3. `entry` 非空
4. 首 entry 为 `Composition`
5. 包含 `Patient`、`Composition`、`Observation`
6. 各 resource 的 `subject.reference` 指向 Patient

**未检查**：Profile 合规、Terminology 绑定、Cardinality 完整、官方 Schema。

### 5.4 外部 Validator 适配

```bash
# 设置外部 CLI（示例）
export PAPER2_FHIR_VALIDATOR_CMD='java -jar validator_cli.jar {path} -version 4.0.1'
python3 doctor/paper2/experiments/run_fhir_validation_replay.py --trials 24
```

| 模式 | 标识 | 当前状态 |
|------|------|----------|
| local-structural | 默认 | ✅ 已跑 120 Bundle |
| external-cli | 环境变量指定 | ⏳ blocked（接口就绪） |

### 5.5 B4 repair_fhir 流程

```
build_fhir_bundle(omit_observation=True)   # 故意缺失
  → validate_bundle() → invalid
  → repair_fhir_bundle()                   # 补齐 Observation
  → validate_bundle() → valid
```

FHIR replay 结果：B0–B3 valid rate = 0.75，B4 = **1.00**（local 模式）。

---

## 6. 答辩速查：架构 + FHIR 五句话

1. **B0 线性生成**在冲突场景幻觉率 62.5%，证明必须门控。
2. **B2 KG 门控**通过确定性路由把幻觉压到 0，每个决策有 kg_matches 证据。
3. **状态图**优于一次 LLM 调用，因为 JSONL 可审计、B0–B4 可消融。
4. **FHIR** 遵循 document Bundle 结构，本地校验覆盖 Composition-first 等关键约束。
5. **当前 MVP** 的 FHIR 结果是 local-structural，非 HL7 官方认证；readiness audit 已标记 blocked。

---

## 7. 与论文 I §07 的呼应

论文 I [07_LangGraph与FSM对比深度分析.md](../../paper1/study/07_LangGraph与FSM对比深度分析.md) 论证了：

> LangGraph 路由开销可忽略（占 RTT 0.004%），价值在于 checkpoint、可视化、论文 II 复用。

论文 II 将这一论证**扩展到多 Agent 场景**：

| 论文 I 结论 | 论文 II 扩展 |
|-------------|-------------|
| 路由开销可忽略 | 多 Agent 编排开销在 MVP 仍 < 50 ms/trial |
| LangGraph 可复用 | 同一范式，状态对象从 q_img 扩展到 Paper2State |
| 条件边可视化 | 六路由分支可生成流程图 |
| checkpoint 持久化 | 未来多轮补问/补拍需要 |

---

## 8. 未来工作路线图

| 阶段 | 任务 | 解锁的 gate |
|------|------|-------------|
| P2-3 | 真机 Skills 联调 | franka_loop |
| P2-4 | 官方 FHIR validator | fhir_official |
| P2-5 | MIMIC 派生数据主实验 | public_dataset |
| P2-6 | 真实专家盲审 | expert_review |
| P2-2 | 授权本体 + 大图 GNN | ontology_mapping, large_gnn |

---

**返回目录** → [README.md](./README.md)
