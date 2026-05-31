# 论文 II / franka_ros2 科研技术方案与工作计划

> **版本**：P2-plan-20260531  
> **日期**：2026-05-31  
> **参考文件**：`docs-zh/paper2/石洪雷_博士学位论文IIn_SCI一区聚焦科研实施方案_V2.md`  
> **项目仓库**：`/home/ros/work/bot-paper2/franka_ros2`  
> **目标读者**：博士课题执行人员、AI 编程代理、论文 II 合作者  
> **安全说明**：运行密码、API Key、临床数据访问凭据等均不得写入本文档、代码、日志或提交记录。

---

## 1. 结论先行

论文 II 的高阶目标是构建“LangGraph 多智能体 + 知识图谱约束 + 工具调用 + 具身重采样”的闭环系统，用于多模态医疗记录合成中的冲突识别、事实对齐和反幻觉。结合当前 `franka_ros2` 的真实状态，下一步不应直接把完整医学大模型、FHIR 生成器、GNN 知识图谱训练代码全部塞入 ROS 2 包，而应采用分层路线：

| 层级 | 推荐承载位置 | 当前职责 |
|---|---|---|
| **认知研究层** | 新建 `doctor/paper2/` 或同级研究目录 | LangGraph 多 Agent、KG/GNN、FHIR 映射、公开数据集回放、主实验脚本 |
| **边缘 API 层** | 本仓 `franka_api_server/` | 图像质量评估、具名 Skills、状态查询、WebSocket、未来 paper2 工具接口 |
| **具身执行层** | 本仓 `franka_*` ROS 2 包 | FR3/MoveIt/Gazebo/fake hardware/真实硬件动作执行 |
| **证据与复现层** | `docs-zh/paper2/`、`logs/`、`doctor/paper2/experiments/` | 技术方案、任务清单、JSONL 轨迹、CSV 指标、图表生成说明 |

本仓当前已经具备论文 II 的“具身闭环底座”雏形：`vision/evaluate`、`motion/skills`、`RosBridge.send_ptp_motion`、`doctor/paper1/langgraph_router` 和 `scripts/paper1_closed_loop.sh` 已形成“感知评分 -> 路由决策 -> 具名位姿 Skill -> JSONL 日志”的最小闭环。论文 II 应在这个基础上扩展为“语义冲突评分 -> 临床质疑节点 -> 工具调用/补拍 -> 结构化 EMR/FHIR 生成”的多轮闭环。

---

## 2. 项目证据与 GitNexus 观察

### 2.1 GitNexus 索引状态

已在当前工作区执行 `npx gitnexus status`，结果显示：

| 项 | 结果 |
|---|---|
| 仓库路径 | `/home/ros/work/bot-paper2/franka_ros2` |
| 索引时间 | 2026-05-31 12:03:03 |
| 索引提交 | `ca3b529` |
| 当前提交 | `ca3b529` |
| 状态 | up-to-date |
| 规模 | 542 files, 6214 symbols, 9119 edges, 156 execution flows |

说明：当前 GitNexus 索引可作为本方案的代码理解依据。本文是新增文档，不修改函数/类/方法符号，因此不触发“修改符号前必须做 impact analysis”的约束。

### 2.2 GitNexus 查询到的关键执行流

| 研究相关概念 | GitNexus 命中执行流 | 关键符号 | 对论文 II 的意义 |
|---|---|---|---|
| 图像质量评估 | `proc_30_evaluate_image_bytes` | `paper1_iqa.evaluate_image_path()` | 可扩展为 Vision Agent 的工具接口 |
| 具名动作 Skill | `proc_104_execute_skill` | `routers.motion.execute_skill()` | 可作为 Action Agent 的具身工具执行入口 |
| 关节运动执行 | `proc_107_send_ptp_motion` | `RosBridge.send_ptp_motion()` | 可承接补拍、视角微调、采集重试动作 |
| 论文 I 闭环 trial | `doctor/paper1/langgraph_router/graph.py::run_trial` | `compute_q()`、`route()`、`go_to_skill()` | 可升级为论文 II 的多 Agent 状态图 |
| 主实验矩阵 | `doctor/paper1/experiments/run_matrix.py` | `simulate_frame()`、`run_seed()` | 可复用“离线回放 + 扰动注入 + CSV 汇总”的实验范式 |

### 2.3 当前代码可直接复用的能力

| 能力 | 当前文件 | 已有行为 | 论文 II 扩展方向 |
|---|---|---|---|
| FastAPI 服务 | `franka_api_server/franka_api_server/app.py` | 注册 status/ws/motion/gripper/vision 路由；`PAPER1_MODE` 时禁用 controller | 增加 paper2 研究路由或保持工具路由稳定供外部 Agent 调用 |
| 图像评估 | `franka_api_server/franka_api_server/routers/vision.py` | 支持 multipart 文件或受限 `image_path`，调用 Edge-IQA | 输出更丰富的 `vision_tags`、`q_img`、ROI 质量标记 |
| Paper I IQA 桥接 | `services/paper1_iqa.py` | 子进程或 import 调用 `doctor/paper1/edge_iqa` | 作为 Vision Agent 的质量评分工具 |
| Skills API | `routers/motion.py`、`services/skills_loader.py` | `POST /api/v1/motion/skills/{skill_name}` | 扩展为补拍、偏移、对焦、照明等原子工具 |
| 位姿配置 | `skills/poses.yaml` | `go_to_tongue_pose`、`go_to_face_pose` | 增加 `resample_left/right/up/down`、`inspection_home` |
| ROS 桥接 | `ros_bridge.py` | MoveIt 优先，FollowJointTrajectory/PTP 回退 | 承接 Action Agent 的可审计动作执行 |
| 闭环脚本 | `scripts/paper1_closed_loop.sh`、`scripts/paper1_run_m6.sh` | 生成 JSONL 与 M6 RTT CSV | 改造为 paper2 冲突闭环 trial |

---

## 3. 论文 II 在当前项目中的科研定位

### 3.1 从论文 I 到论文 II 的连续性

论文 I 已经把问题限定为“边侧图像质量评估 + 置信度路由 + FR3 重采样”。论文 II 不应另起炉灶，而应把论文 I 的单一质量阈值闭环升级为多模态语义一致性闭环：

| 维度 | 论文 I | 论文 II |
|---|---|---|
| 状态对象 | `q_img`、`flags`、`retry_count`、`route_decision` | 文本症状、视觉标签、时间戳、工具结果、KG 置信度、FHIR 草稿 |
| 路由条件 | `q_img >= tau` | `gamma_conflict >= tau_gating` 且 FHIR/KG 证据一致 |
| 回退动作 | `resample_edge` | 补拍、补问、检索、FHIR 校验、人工审阅挂起 |
| 主要风险 | 图像模糊导致无效上传 | LLM 幻觉、文本/视觉冲突、长上下文遗忘 |
| 主要证据 | RTT、有效采集率、上传减少 | 冲突检出率、幻觉率下降、FHIR 有效率、专家审查一致性 |

### 3.2 当前项目的论文 II 贡献边界

`franka_ros2` 在论文 II 中建议定位为“具身边缘执行面 + 可复现机器人闭环证据”，不承担全部医学信息学算法训练。这样可以保证 ROS 2 工程边界清晰，并使论文 II 的主实验可在公开数据集上独立复现。

| 本仓应交付 | 本仓不应强行承担 |
|---|---|
| FR3 fake hardware/Gazebo/MoveIt 可执行闭环 | 大规模 LLM 训练 |
| `franka_api_server` 工具接口与审计日志 | 医学本体全量许可证管理 |
| 具名 Skills 与动作安全护栏 | 临床真实数据脱敏和伦理审批主体 |
| paper2 closed-loop JSONL 样例 | 主论文全部医学 benchmark |
| 机器人补拍与状态监测可视化 | 医生双盲评审的组织管理 |

---

## 4. 总体技术架构

### 4.1 三层闭环

```text
┌────────────────────────────────────────────────────────────────────┐
│  Cognition / Research Layer: doctor/paper2                          │
│  LangGraph StateGraph                                                │
│  ├─ Symptom Agent: 文本症状抽取、补问生成                             │
│  ├─ Vision Agent: 图像质量、ROI、视觉体征标签                         │
│  ├─ KG Conflict Agent: 本体/KG/GNN 置信度与冲突门控                   │
│  ├─ EMR/FHIR Agent: 结构化病历草稿与 FHIR 校验                        │
│  └─ Action Agent: 工具选择、补拍/补问/检索动作                         │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ HTTP / JSON / JSONL
┌──────────────────────────────▼─────────────────────────────────────┐
│  Edge API Layer: franka_api_server                                  │
│  ├─ POST /api/v1/vision/evaluate                                     │
│  ├─ POST /api/v1/motion/skills/{skill_name}                          │
│  ├─ GET  /api/v1/status/joints, /status/robot                        │
│  ├─ WebSocket /ws                                                    │
│  └─ Future: /api/v1/paper2/tools/*                                    │
└──────────────────────────────┬─────────────────────────────────────┘
                               │ ROS 2 actions/topics
┌──────────────────────────────▼─────────────────────────────────────┐
│  Device Layer: FR3 / MoveIt / Gazebo / ros2_control                  │
│  ├─ MoveGroup action                                                 │
│  ├─ FollowJointTrajectory fallback                                   │
│  ├─ PTPMotion fallback                                               │
│  └─ joint_states / robot_state telemetry                             │
└────────────────────────────────────────────────────────────────────┘
```

### 4.2 统一 Context Object

建议在 `doctor/paper2/langgraph_router/state.py` 定义论文 II 的统一状态对象，并在 JSONL 中逐条落盘。

```python
class Paper2State(TypedDict, total=False):
    trial_id: str
    case_id: str
    turn_id: int
    symptom_text: str
    symptom_entities: list[dict]
    image_path: str
    q_img: float
    vision_tags: list[dict]
    kg_matches: list[dict]
    gamma_conflict: float
    tau_gating: float
    conflict_type: str
    route_decision: str
    tool_calls: list[dict]
    skill_name: str
    robot_status: dict
    emr_draft: dict
    fhir_bundle: dict
    validation_errors: list[str]
    timestamps: dict[str, str]
    latency_ms: dict[str, float]
```

关键要求：

| 字段组 | 最小必填 | 说明 |
|---|---|---|
| 身份 | `trial_id`, `case_id`, `turn_id` | 保证多轮闭环可追踪 |
| 多模态输入 | `symptom_text`, `image_path`, `q_img` | 对齐文本与视觉 |
| 冲突证据 | `vision_tags`, `kg_matches`, `gamma_conflict` | 支撑 GN-KGCAD 消融 |
| 路由与动作 | `route_decision`, `tool_calls`, `skill_name` | 支撑 Toolformer/Action Agent 研究 |
| 输出资产 | `emr_draft`, `fhir_bundle`, `validation_errors` | 支撑 EHR/FHIR 论文指标 |
| 审计 | `timestamps`, `latency_ms` | 支撑系统工程指标与复现 |

### 4.3 状态机路由

论文 II 第一版不建议直接上复杂 GNN 训练，应先实现可解释的规则/KG stub，再替换为 GAT/GNN。最小状态图如下：

```text
capture_case
  └─► symptom_agent
        └─► vision_agent
              └─► kg_conflict_gate
                    ├─ gamma >= tau ─► emr_fhir_agent ─► validate_and_log ─► done
                    ├─ vision_low    ─► action_agent_resample ─► vision_agent
                    ├─ text_low      ─► symptom_followup_agent ─► kg_conflict_gate
                    └─ fhir_invalid  ─► emr_repair_agent ─► validate_and_log
```

路由枚举建议固定为：

| `route_decision` | 含义 | 触发动作 |
|---|---|---|
| `generate_emr` | 多模态证据一致 | 进入 EMR/FHIR 生成 |
| `resample_vision` | 视觉质量低或视觉标签与文本冲突 | 调用 `motion/skills/*` 补拍 |
| `ask_followup` | 文本症状缺关键实体 | 生成补问或模拟补问答案 |
| `query_kg` | 需要知识图谱补充证据 | 查询本体/KG |
| `repair_fhir` | FHIR schema 或字段映射失败 | 修复结构化输出 |
| `human_review` | 多轮仍不收敛 | 标记人工审阅 |
| `fail_safe` | 工具失败或超过重试次数 | 安全退出并保留证据 |

---

## 5. 关键技术模块方案

### 5.1 Paper2 Agent 研究层

建议新增目录：

```text
doctor/paper2/
├── README.md
├── pyproject.toml
├── langgraph_router/
│   ├── state.py
│   ├── graph.py
│   ├── routing.py
│   └── run.py
├── agents/
│   ├── symptom_agent.py
│   ├── vision_agent.py
│   ├── kg_conflict_agent.py
│   ├── emr_fhir_agent.py
│   └── action_agent.py
├── tools/
│   ├── franka_client.py
│   ├── kg_client.py
│   ├── fhir_validator.py
│   └── dataset_loader.py
├── experiments/
│   ├── configs/
│   ├── logs/
│   ├── results/
│   └── reports/
├── figures/
├── tests/
└── latex/
```

最小实现顺序：

1. 复用 `doctor/paper1/sim/franka_bridge/client.py` 的 HTTP client 方式，新建 `tools/franka_client.py`。
2. 在 `langgraph_router/graph.py` 中跑通单 trial 状态流，不依赖真实 LLM。
3. 使用规则或本地 JSON KG stub 生成 `gamma_conflict`。
4. 以 JSONL 记录每个节点的输入、输出、工具调用和耗时。
5. 通过配置切换基线：线性 LLM、普通 self-reflection、KG-gated closed loop。

### 5.2 Vision Agent

第一阶段只使用现有 `POST /api/v1/vision/evaluate`，返回：

```json
{
  "q_img": 0.72,
  "flags": ["blur"],
  "t_iqa_ms": 12.4,
  "threshold_tau": 0.55,
  "meta": {"scorer": "edge_iqa", "mode": "subprocess"}
}
```

第二阶段扩展为：

| 扩展字段 | 来源 | 用途 |
|---|---|---|
| `roi_quality` | 传统 CV 或 segmentation stub | 判断是否需要补拍 |
| `vision_tags` | 规则/模型输出 | 与文本实体做 KG 对齐 |
| `occlusion_ratio` | 图像退化脚本或检测模型 | 遮挡消融 |
| `cam_pose_hint` | FR3 当前 joint state / TF | 分析具身位姿与图像质量关系 |

不要在第一版承诺已经实现 TGD-VAM 交叉注意力模型。建议先用公开数据集和退化脚本构造“文本先验提升 ROI 定位”的可复现实验，再决定是否训练深度模型。

### 5.3 KG Conflict Agent / GN-KGCAD

分三步走：

| 阶段 | 技术实现 | 验收证据 |
|---|---|---|
| P2-KG-1 | JSON/YAML 小型实体关系图，规则相似度 | 100 个 synthetic conflict case 的路由正确率 |
| P2-KG-2 | 本体映射表：症状、体征、疾病、FHIR 字段 | `kg_edges.csv`、`entity_map.csv`、覆盖率报告 |
| P2-KG-3 | GNN/GAT 嵌入或图相似度模型 | `gamma_conflict` 消融曲线、AUC/F1 |

第一版 `gamma_conflict` 可以定义为：

```text
gamma_conflict = w_text * entity_completeness
               + w_vision * vision_quality
               + w_kg * kg_consistency
               - w_conflict * contradiction_penalty
```

其中：

| 分量 | 解释 |
|---|---|
| `entity_completeness` | 主诉文本是否包含必要实体 |
| `vision_quality` | `q_img` 与 ROI 质量 |
| `kg_consistency` | 文本实体和视觉标签在 KG 中是否存在可信边 |
| `contradiction_penalty` | 人工注入或模型识别的矛盾强度 |

门控规则：

```text
if gamma_conflict >= tau_gating:
    route_decision = "generate_emr"
elif vision_quality < tau_vision:
    route_decision = "resample_vision"
elif entity_completeness < tau_text:
    route_decision = "ask_followup"
else:
    route_decision = "query_kg"
```

### 5.4 Action Agent 与具身 Skills

当前已有 Skills：

| Skill | 当前映射 | 用途 |
|---|---|---|
| `go_to_tongue_pose` | `tongue_pose` | 舌象采集位姿 |
| `go_to_face_pose` | `face_pose` | 面部采集位姿 |

论文 II 建议新增 Skills，但要分批标定：

| 新 Skill | 目的 | 是否需要真机 |
|---|---|---|
| `go_to_inspection_home` | 统一起始位姿 | fake hardware 可先做 |
| `resample_tongue_left` | 遮挡/偏心时左偏重拍 | fake hardware 可先做 |
| `resample_tongue_right` | 遮挡/偏心时右偏重拍 | fake hardware 可先做 |
| `resample_tongue_close` | ROI 过小时接近 | 真机前必须做碰撞/速度审核 |
| `resample_tongue_far` | 过曝/失焦时后撤 | 真机前必须做碰撞/速度审核 |
| `set_lighting_level` | 补光控制 | 需要实际灯光硬件或 mock |

安全不变量：

1. 研究层只调用具名 Skill，不直接发裸关节角。
2. `max_velocity_scaling` 默认不超过现有 `0.3`，真机前单独降速。
3. 每次补拍动作必须写入 JSONL：`skill_name`、输入原因、返回状态、耗时。
4. 连续重试超过 `K` 次后进入 `human_review` 或 `fail_safe`。

### 5.5 Toolformer-Med / 工具调用策略

论文参考文件中提出 Toolformer-Med 自监督工具调用。当前项目建议先做“可控工具策略实验”，再做自监督微调：

| 阶段 | 做法 | 论文可写成 |
|---|---|---|
| Tool-0 | 手工规则工具选择 | 工程基线 |
| Tool-1 | LLM 函数调用或 ReAct 选择工具，但工具白名单固定 | Agentic tool-use prototype |
| Tool-2 | 离线采样工具调用位置，计算有/无工具的损失或指标差 | Toolformer-inspired filtering |
| Tool-3 | 训练小模型或策略分类器预测工具调用 | Toolformer-Med 完整实验 |

工具白名单建议：

| 工具 | 输入 | 输出 |
|---|---|---|
| `evaluate_image` | `image_path` | `q_img`, `flags`, `vision_tags` |
| `execute_skill` | `skill_name` | `accepted/failed`, `task_id` |
| `query_kg` | `entities` | `kg_matches`, `consistency_score` |
| `ask_followup` | `missing_entity` | `followup_question`, `simulated_answer` |
| `validate_fhir` | `bundle_json` | `valid`, `errors` |
| `repair_emr` | `draft`, `errors` | `repaired_draft` |

---

## 6. 实验设计

### 6.1 数据路线

优先保证“公开、可复现、许可证清晰”。建议按三类数据组织：

| 数据类型 | 第一版来源 | 用途 |
|---|---|---|
| 舌/面视觉样本 | 复用论文 I 的 TCM-Tongue synthetic/退化集，或公开舌象/面部医学图像数据 | 图像质量、遮挡、重拍策略 |
| 文本症状/EHR 样本 | 公开医疗问答、MIMIC 类受控访问数据、合成病例模板 | 症状实体抽取、补问、EMR 草稿 |
| 本体/KG | 自建小型实体关系表，后续映射 ICD/SNOMED/FHIR | 冲突门控、FHIR 字段约束 |

注意：受控医疗数据、SNOMED CT 等资源可能涉及访问许可，不能在仓库中直接提交原始数据或许可证受限内容。仓库只提交下载说明、字段映射脚本、脱敏样例和 hash/统计。

### 6.2 基线设置

| 编号 | 名称 | 特征 | 目的 |
|---|---|---|---|
| B0 | Linear EMR | 输入文本/视觉后一次性生成 EMR | 测 LLM 幻觉与冲突脆弱性 |
| B1 | Self-Reflection | LLM 自我反思但无 KG/具身工具 | 对比普通循环 |
| B2 | KG-Gated | 加 KG 规则门控，但不调用机器人补拍 | 分离 KG 贡献 |
| B3 | Embodied Closed Loop | KG 门控 + Action Agent + Skills 补拍/补问 | 完整方法 |
| B4 | Toolformer-Inspired | 在 B3 上增加工具调用过滤策略 | 工具调用贡献 |

### 6.3 指标体系

| 指标 | 定义 | 证据文件 |
|---|---|---|
| `conflict_detection_f1` | 注入冲突的检出 F1 | `experiments/results/conflict_detection.csv` |
| `hallucination_rate` | 输出中无证据医学断言比例 | `experiments/results/hallucination_eval.csv` |
| `kg_gate_auc` | `gamma_conflict` 区分一致/冲突样本能力 | `experiments/results/kg_gate_auc.csv` |
| `fhir_valid_rate` | FHIR Bundle schema/字段通过率 | `experiments/results/fhir_validation.csv` |
| `resample_success_rate` | 补拍后 `q_img` 或 ROI 达标比例 | `experiments/results/resample.csv` |
| `closed_loop_latency_ms` | 单 trial 端到端耗时 | JSONL `latency_ms` |
| `tool_helpfulness_delta` | 有工具相对无工具的指标提升 | `experiments/results/tool_ablation.csv` |

### 6.4 冲突注入

建议先用可控脚本构造冲突，不依赖真实临床矛盾判断：

| 冲突类型 | 构造方法 | 期望路由 |
|---|---|---|
| 视觉低质 | 对图像注入 blur/occlusion/exposure 退化 | `resample_vision` |
| 文本缺失 | 删除主诉中的关键症状实体 | `ask_followup` |
| 文本-视觉矛盾 | 文本标签与视觉标签随机错配 | `query_kg` 或 `ask_followup` |
| FHIR 缺字段 | 删除 required/核心字段 | `repair_fhir` |
| 工具失败 | mock API 返回 failed/timeout | `fail_safe` |

### 6.5 JSONL 证据格式

每个 trial 至少写一行 summary，复杂调试可写 node-level event。

```json
{
  "trial_id": "p2_000001",
  "case_id": "case_0001",
  "baseline": "B3",
  "q_img": 0.42,
  "symptom_entities": [{"name": "fever", "source": "text"}],
  "vision_tags": [{"name": "tongue_coating_pale", "score": 0.71}],
  "gamma_conflict": 0.38,
  "tau_gating": 0.65,
  "route_decision": "resample_vision",
  "tool_calls": [
    {
      "tool": "execute_skill",
      "args": {"skill_name": "go_to_tongue_pose"},
      "status": "accepted",
      "latency_ms": 18.2
    }
  ],
  "fhir_valid": false,
  "latency_ms": {"total": 141.7},
  "timestamp": "2026-06-15T09:00:00Z"
}
```

---

## 7. 当前仓库的实施任务清单

### Phase P2-0：证据冻结与工程边界确认（2026-06-01 至 2026-06-07）

| ID | 任务 | 位置 | 验收 |
|---|---|---|---|
| P2-0-1 | 固化本方案与 README | `docs-zh/paper2/` | 文件存在，能说明边界和路线 |
| P2-0-2 | 记录 GitNexus 状态 | `docs-zh/paper2/` 或周报 | 包含索引提交、symbols、flows |
| P2-0-3 | 复核论文 I 当前闭环 | `scripts/paper1_closed_loop.sh` | 能生成 10 trial JSONL 或记录阻塞 |
| P2-0-4 | 确定 `doctor/paper2` 是否纳入本仓 | 项目决策 | 有目录策略，不混入 ROS 包 |
| P2-0-5 | 建立 secrets 规则 | 文档/环境变量 | 密码不写入仓库 |

### Phase P2-1：Paper2 最小状态图（2026-06-08 至 2026-06-21）

| ID | 任务 | 建议文件 | 验收 |
|---|---|---|---|
| P2-1-1 | 新建 `doctor/paper2` 骨架 | `doctor/paper2/` | `pytest` 可运行空测试 |
| P2-1-2 | 定义 `Paper2State` | `langgraph_router/state.py` | 类型字段覆盖 §4.2 |
| P2-1-3 | 实现规则路由 | `langgraph_router/routing.py` | 路由枚举全覆盖 |
| P2-1-4 | 实现单 trial runner | `langgraph_router/run.py` | 生成 `paper2_run_001.jsonl` |
| P2-1-5 | 复用 franka client | `tools/franka_client.py` | 可调用 `/vision/evaluate` 与 `/motion/skills` |

### Phase P2-2：KG 冲突门控 MVP（2026-06-22 至 2026-07-12）

| ID | 任务 | 建议文件 | 验收 |
|---|---|---|---|
| P2-2-1 | 小型 KG schema | `kg/kg_stub.yaml` | 30 个症状/体征关系 |
| P2-2-2 | 实体归一化 | `tools/entity_normalizer.py` | 规则测试通过 |
| P2-2-3 | `gamma_conflict` 计算 | `agents/kg_conflict_agent.py` | 单元测试覆盖一致/冲突/缺失 |
| P2-2-4 | 冲突注入脚本 | `experiments/inject_conflicts.py` | 输出可复现实验 CSV |
| P2-2-5 | B0/B1/B2 对比 | `experiments/run_conflict_ablation.py` | 生成 F1/AUC 表 |

### Phase P2-3：具身自愈闭环（2026-07-13 至 2026-08-02）

| ID | 任务 | 位置 | 验收 |
|---|---|---|---|
| P2-3-1 | 扩展 Skills 清单 | `franka_api_server/.../skills/poses.yaml` | 新 skill 在 fake hardware 下可调用 |
| P2-3-2 | Action Agent 工具选择 | `doctor/paper2/agents/action_agent.py` | 视觉低质时选择补拍 |
| P2-3-3 | closed-loop 脚本 | `scripts/paper2_closed_loop.sh` | 10 trial JSONL |
| P2-3-4 | M6 风格 RTT 汇总 | `doctor/paper2/experiments/summarize_closed_loop.py` | p50/p95 CSV |
| P2-3-5 | 安全退出 | 路由逻辑 | 超过 K 次进入 `human_review/fail_safe` |

如需修改 `execute_skill()`、`send_ptp_motion()` 或 Skills loader，必须按 AGENTS.md 要求先运行 GitNexus impact analysis，并对 HIGH/CRITICAL 风险暂停告警。

### Phase P2-4：FHIR/EMR 结构化输出（2026-08-03 至 2026-08-23）

| ID | 任务 | 建议文件 | 验收 |
|---|---|---|---|
| P2-4-1 | EMR draft schema | `schemas/emr_draft.schema.json` | schema 校验通过 |
| P2-4-2 | FHIR mapping MVP | `tools/fhir_mapper.py` | 可生成 Bundle/Composition/Observation 草稿 |
| P2-4-3 | FHIR validator wrapper | `tools/fhir_validator.py` | invalid case 有错误列表 |
| P2-4-4 | repair loop | `agents/emr_fhir_agent.py` | 修复后 valid rate 提升 |
| P2-4-5 | 输出脱敏样例 | `experiments/samples/` | 不含真实隐私信息 |

### Phase P2-5：工具调用消融与论文图表（2026-08-24 至 2026-09-20）

| ID | 任务 | 输出 | 验收 |
|---|---|---|---|
| P2-5-1 | B0-B4 全量实验 | `experiments/results/*.csv` | 每个 baseline 至少 3 seeds |
| P2-5-2 | 工具调用有效性统计 | `tool_ablation.csv` | 有/无工具指标差 |
| P2-5-3 | 幻觉率评估 | `hallucination_eval.csv` | 规则或人工标注口径固定 |
| P2-5-4 | 图表脚本 | `figures/*.py` | 可重绘论文图 |
| P2-5-5 | 初稿结果段 | `latex/sections/results.tex` | 数字全部来自 CSV |

### Phase P2-6：论文与专利材料（2026-09-21 至 2026-10-31）

| ID | 任务 | 输出 | 验收 |
|---|---|---|---|
| P2-6-1 | 方法章节初稿 | `latex/sections/method.tex` | 状态图、KG 门控、工具调用公式一致 |
| P2-6-2 | 系统章节 | `latex/sections/system.tex` | 与 `franka_ros2` 代码边界一致 |
| P2-6-3 | 专利交底 | `patent/paper2_disclosure.md` | 覆盖冲突门控 + 自愈补拍 |
| P2-6-4 | 复现实验说明 | `REPRODUCE_paper2.md` | 第三方可跑 synthetic MVP |
| P2-6-5 | 投稿路线复核 | 周报/清单 | 目标期刊和伦理/数据许可明确 |

---

## 8. 近期两周可执行任务

| 日期 | 任务 | 具体动作 |
|---|---|---|
| 2026-06-01 | 建立 paper2 骨架 | 新建 `doctor/paper2`、`README.md`、`pyproject.toml`、`tests/` |
| 2026-06-02 | 状态对象与 JSONL | 实现 `Paper2State`、日志 writer、样例 JSONL |
| 2026-06-03 | Franka API client | 从 paper1 client 复制并改名，保留 `evaluate_image`、`go_to_skill` |
| 2026-06-04 | 规则 KG stub | 写 `kg_stub.yaml` 与 `kg_conflict_agent.py` |
| 2026-06-05 | 单 trial 状态图 | 跑通 capture -> symptom -> vision -> kg_gate -> route |
| 2026-06-06 | 路由测试 | 覆盖 `generate_emr/resample_vision/ask_followup/query_kg/fail_safe` |
| 2026-06-07 | 周报证据 | 输出 `paper2_run_001.jsonl` 与 `P2-0/P2-1` 验收表 |
| 2026-06-08 | 冲突注入 | 实现文本-视觉错配与视觉退化样本 |
| 2026-06-09 | B0/B2 初版 | 比较线性生成与 KG-gated 路由 |
| 2026-06-10 | API 联调 | 启动 `franka_api_server`，确认工具调用返回被写入 JSONL |
| 2026-06-11 | Skills 规划 | 确认是否新增 resample 位姿，真机前仅 fake hardware |
| 2026-06-12 | 指标汇总 | 输出 `conflict_detection.csv`、`closed_loop_latency.csv` |
| 2026-06-13 | 文档更新 | 把实际结果补入 `docs-zh/paper2/` |
| 2026-06-14 | 阶段复盘 | 决定是否进入 GNN/FHIR 深化 |

---

## 9. 验收门槛

### 9.1 工程验收

| 门槛 | 命令或证据 |
|---|---|
| GitNexus 索引可用 | `npx gitnexus status` |
| API 服务可启动 | `scripts/startapi.sh` 或 `ros2 launch franka_api_server api_server.launch.py` |
| 视觉工具可用 | `POST /api/v1/vision/evaluate` 返回 `q_img` |
| Skill 工具可用 | `GET /api/v1/motion/skills` 返回已有 skill |
| paper2 runner 可用 | `python -m langgraph_router.run --trials 10 --log ...` |
| JSONL 可校验 | 每行包含 `trial_id/route_decision/gamma_conflict/tool_calls` |

### 9.2 科研验收

| 阶段 | 最低验收 |
|---|---|
| MVP | 10 trial synthetic conflict，至少出现 3 种路由 |
| KG 消融 | B2 相对 B0 的冲突检出 F1 提升 |
| 具身闭环 | B3 能在视觉低质样本中调用 `go_to_tongue_pose` 或扩展补拍 skill |
| FHIR 输出 | 至少一种结构化输出 schema 可校验 |
| 论文图表 | 所有数字可从 CSV/JSONL 重算 |

---

## 10. 风险与控制

| 风险 | 影响 | 控制策略 |
|---|---|---|
| 把医学大模型逻辑混入 ROS 包 | 构建复杂、边界混乱 | 研究层放 `doctor/paper2`，ROS 包只提供工具接口 |
| 数据/本体许可证不清 | 无法投稿或开源 | 原始数据不入仓，只提交脚本、hash、脱敏样例 |
| LLM 输出不可复现 | 指标不稳定 | 先做规则/stub/MVP，LLM 结果固定 seed 和缓存 |
| 真机动作风险 | 设备/人员风险 | fake hardware 先验收，真机前降速、限位、人工确认 |
| 工具调用过度循环 | trial 卡死 | `K` 次重试上限，进入 `human_review/fail_safe` |
| 幻觉率定义主观 | 论文说服力不足 | 固定证据词表、KG 边、人工抽样复核协议 |

---

## 11. 文档与代码交付清单

| 类型 | 文件 | 状态 |
|---|---|---|
| 规划 | `docs-zh/paper2/论文II_franka_ros2_科研技术方案与工作计划_20260531.md` | 本文 |
| 目录索引 | `docs-zh/paper2/README.md` | 建议新增 |
| 参考方案 | `docs-zh/paper2/石洪雷_博士学位论文IIn_SCI一区聚焦科研实施方案_V2.md` | 已存在 |
| 研究层代码 | `doctor/paper2/` | 下一阶段新增 |
| 闭环脚本 | `scripts/paper2_closed_loop.sh` | 下一阶段新增 |
| 实验日志 | `doctor/paper2/experiments/logs/*.jsonl` | 下一阶段生成 |
| 结果表 | `doctor/paper2/experiments/results/*.csv` | 下一阶段生成 |

---

## 12. AI Agent 执行规则

1. 文档改动可直接执行；代码符号改动前按 AGENTS.md 运行 GitNexus impact analysis。
2. 不提交密码、API Key、临床隐私、受控数据原文。
3. 任何新增 paper2 API 必须有最小测试和 JSONL 证据字段说明。
4. 修改 `franka_api_server` 的路由、模型、ROS 桥接时，必须保持论文 I 当前接口兼容。
5. 实验结果写作时，所有论文数字必须能回溯到 CSV/JSONL，不得手填不可追溯数字。

---

## 13. 最小下一步

下一步建议直接执行：

```bash
mkdir -p doctor/paper2/{langgraph_router,agents,tools,experiments/{configs,logs,results,reports},figures,tests,kg,schemas}
```

然后优先实现：

1. `doctor/paper2/langgraph_router/state.py`
2. `doctor/paper2/langgraph_router/routing.py`
3. `doctor/paper2/tools/franka_client.py`
4. `doctor/paper2/agents/kg_conflict_agent.py`
5. `doctor/paper2/langgraph_router/run.py`
6. `scripts/paper2_closed_loop.sh`

达到的第一个里程碑应是：**在不接真实 LLM、不接真实临床数据的情况下，用 synthetic 文本-视觉冲突样本跑出 10 行 paper2 JSONL，并证明系统能在 `generate_emr / resample_vision / ask_followup / human_review` 之间做可解释路由。**
