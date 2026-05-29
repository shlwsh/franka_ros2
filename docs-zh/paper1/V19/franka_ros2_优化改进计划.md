# franka_ros2 科研优化改进计划（对齐论文 I · V19）

> **版本**：V19-franka | 2026-05-29  
> **依据**：[论文1_V19.md](./论文1_V19.md)、[科研规划_论文I_V19.md](./科研规划_论文I_V19.md)、[论文1_V19_tasks.json](./论文1_V19_tasks.json)  
> **适用范围**：WSL `/root/work/franka_ros2`（闭环执行轨）；算法主轨仍在 `ppt-builder/doctor/paper1`  
> **目标**：在 **2026-09-30** 投稿前，使本仓库满足论文 §3 / §5.5 / Supplementary 对「云–边–端可复现闭环」的验收要求，且**不稀释** Edge-IQA + LangGraph 的算法贡献边界。

---

## 1. 执行摘要

论文 I 的**主实验（M1–M3、Fig.5–7）**必须在 `doctor/paper1` 离线完成；`franka_ros2` 的角色是：

1. 提供 **§3 系统架构** 中 Device–Edge 层的可运行实例（FastAPI 边网关 + FR3 Skills + 可选 Gazebo 相机）；
2. 提供 **辅轨 M6 / §5.5**：假硬件或 Gazebo 下 **≥50 次 trial** 的闭环 RTT 趋势，与离线 M1 **方向一致**；
3. 产出可投稿的 **JSONL 轨迹**（`t_capture`, `t_iqa`, `t_route`, `route_decision` 等），支撑「LangGraph 可测试、可日志复现」论述。

**当前匹配度（工程底座）**：约 **50%** — 具备 MoveIt 假硬件、`franka_api_server`、Gazebo 包与联调脚本，但**缺少** V19 规定的 vision 网关、命名 Skills、笛卡尔/预定义位姿 API、闭环脚本与论文级计时日志。

**优化原则（必须遵守）**：

| 原则 | 说明 |
|------|------|
| 算法不进 ROS 包 | `edge_iqa`、`langgraph_router` 仅驻留 `doctor/paper1`；本仓通过 **HTTP 子进程/导入** 调用 |
| 弱化阻抗 | **禁止**在论文 I 实验中使用 `routers/controller.py`（刚度/碰撞） |
| 双轨分离 | 主图数字来自离线矩阵；franka 仅辅轨，避免「仿真数据冒充主实验」 |
| 薄层扩展 | 优先改 `franka_api_server` + `scripts/`，避免 fork `franka_hardware` |

---

## 2. 现状评估（2026-05-29）

### 2.1 已具备、可直接复用

| 模块 | 路径 | 论文 I 用途 |
|------|------|-------------|
| 边侧 HTTP 网关 | `franka_api_server/` | §3.2 Edge gateway 原型（:8000 REST/WS） |
| ROS 桥接 | `franka_api_server/ros_bridge.py` | PTP 关节运动、错误恢复 |
| 一键联调 | `scripts/testall.sh` | F0-02 冒烟（MoveIt fake HW + API） |
| MoveIt 假硬件 | `franka_fr3_moveit_config/` + `scripts/start.sh` | `resample_edge` 位姿重拍 |
| Gazebo 仿真 | `franka_gazebo_bringup/` | P1-T03 采集辅轨（替代 Webots） |
| 关节/机器人状态 | `routers/status.py`, `routers/ws.py` | RTT 日志「执行段」时间戳 |
| 运动 API（关节） | `POST /api/v1/motion/move_joints` | 可映射 `poses.yaml` → 关节目标 |
| 中文运维文档 | `docs-zh/`, `AGENTS.md` | 团队执行与 AI 协作 |

### 2.2 与 V19 要求的差距（须补齐）

| V19 要求 | 当前状态 | 影响 |
|----------|----------|------|
| `POST /api/v1/vision/evaluate` | **未实现** | 无法在边侧演示 Edge-IQA；F2-01 阻塞 |
| `skills/poses.yaml`（`tongue_pose` / `face_pose`） | **未实现** | 无法表达「舌位/面位重拍」Skills |
| `move_to_pose` 或具名 Skill API | **仅有** `move_joints` | F1-01 验收不通过 |
| `scripts/paper1_closed_loop.sh` | **未实现** | F3-01、M6 辅轨无法一键复现 |
| `PAPER1_ROOT` 与 `doctor/paper1` 桥接 | **未文档化/未封装** | 双仓联调成本高 |
| 闭环 JSONL（LangGraph 字段） | **无** | §4.3、Supp. 缺样例 |
| Gazebo → `capture_001.png` 流水线 | **未固化** | P1-T03 每次手工 |
| RTT 分段计时（capture/IQA/route） | **无统一 schema** | M6 无法与 M1 对齐 |
| `bun run mygit` / 开发工具链 | **已具备**（近期） | 利于迭代，与论文无直接冲突 |

### 2.3 刻意不做（避免 scope 膨胀）

| 模块 | 原因 |
|------|------|
| `franka_api_server/routers/controller.py` | 阻抗/碰撞属博士论文他章，论文 I **禁用** |
| `franka_mobile` 全栈导航 | 论文 I 不强调移动底盘 |
| 在 `franka_hardware` 内嵌 IQA | 破坏双仓边界 |
| 真机 FR3 大规模实验 | 9 月前非必须；最多 Supp. 1 组 |
| K8s / 完整云诊疗产品 | V19 §1.1 明确不做 |

---

## 3. 目标架构（优化后）

与 [论文1_V19.md](./论文1_V19.md) §3 一致，本仓仅实现 **Device + Edge 执行面**：

```
doctor/paper1（算法主仓）                    franka_ros2（本仓）
┌─────────────────────────────┐            ┌─────────────────────────────┐
│ edge_iqa/scorer.py          │◄─子进程───│ routers/vision.py             │
│ langgraph_router/graph.py   │            │ franka_api_server (FastAPI)   │
│ sim/franka_bridge/client.py │──HTTP────►│ skills/poses.yaml             │
└──────────────┬──────────────┘            │ routers/motion.py + skills    │
               │                           │ ros_bridge → MoveIt           │
               │ resample                  │ franka_gazebo_bringup (可选)──┼──► 图像
               └──────────────────────────►└─────────────────────────────┘
```

| 调用关系 | 说明 |
|----------|------|
| LangGraph → franka_bridge → API | 闭环 HTTP 客户端 |
| vision → scorer | 子进程或 import，算法不进 ROS |
| API → motion → ROS | 预定义 pose / PTP |
| Gazebo → vision | 相机 topic 或 PNG 文件 |

**闭环数据流（辅轨一次 trial）**：

1. `capture`：Gazebo 相机或读取 TCM 图像路径 → 临时 PNG  
2. `edge_iqa`：`POST /vision/evaluate` → `{ q_img, flags, t_iqa_ms }`  
3. `route`：LangGraph（`doctor/paper1`）决策 → `upload_cloud` | `resample_edge` | `fail_safe`  
4. `resample`：`POST /motion/skills/go_to_tongue_pose`（或 `face_pose`）  
5. 写 JSONL：`latency_ms`, `retry_count`, `route_decision`, …

---

## 4. 分阶段改进计划（对齐 F0–F3）

### Phase F0：环境与双仓打通（06.01–06.21）

| 任务 ID | 改进项 | 具体动作 | 验收标准 |
|---------|--------|----------|----------|
| F0-01 | WSL 挂载与路径 | 新增 `docs-zh/paper1/V19/ENV.md`：定义 `PAPER1_ROOT=/mnt/e/work/ppt-builder/doctor/paper1` | `test -d $PAPER1_ROOT/edge_iqa` 或占位 README |
| F0-02 | 构建冒烟 | 固化 `colcon build` + `scripts/testall.sh` 检查清单 | `curl -s http://localhost:8000` 返回 200 |
| F0-03 | 论文模式开关 | 在 `api_server.yaml` 或环境变量增加 `PAPER1_MODE=1`：禁用 controller 路由注册 | 启动日志无 stiffness 端点 |

**交付物**：

- `docs-zh/paper1/V19/ENV.md`
- `scripts/check_paper1_env.sh`（检查 ROS、PAPER1_ROOT、API）

---

### Phase F1：架构与采集 Skills（06.15–07.05）

| 任务 ID | 改进项 | 具体动作 | 验收标准 |
|---------|--------|----------|----------|
| F1-01 | 预定义位姿 | 新增 `franka_api_server/franka_api_server/skills/poses.yaml`：`tongue_pose`, `face_pose`（关节角或笛卡尔，与 FR3 fake HW 一致） | 两次 API 调用可达，误差 &lt; `goal_tolerance` |
| F1-02 | Skills API | 扩展 `routers/motion.py`：`POST /api/v1/motion/skills/{skill_name}`，内部查 yaml → `move_joints` | 对应 F1-01 |
| F1-03 | Vision 占位 | 新增 `routers/vision.py`：`POST /api/v1/vision/evaluate`（multipart 或 path），**占位**返回 `q_score=0.5`, `flags=[]` | OpenAPI 可见；P1-T02 先过接口契约 |
| F1-04 | 注册路由 | `app.py` 挂载 vision、更新 `docs-api/api_specification.md` | `pytest test_api.py` 新增用例 |
| F1-05 | Gazebo 采集 | 新增 `scripts/paper1_gazebo_capture.sh`：启动 Gazebo + 保存 `experiments/debug/capture_001.png` 到 `$PAPER1_ROOT/experiments/debug/` | P1-T03 PNG 存在 |

**目录结构（本仓验收）**：

```
franka_api_server/franka_api_server/
├── routers/vision.py          # 新增
├── skills/poses.yaml          # 新增
├── models/vision.py           # 新增 Pydantic
└── services/paper1_iqa.py     # 新增：调用 PAPER1_ROOT 的 scorer

scripts/
├── paper1_gazebo_capture.sh   # 新增
├── check_paper1_env.sh        # 新增
└── testall.sh                 # 可选：增加 --paper1 快速检查
```

---

### Phase F2：Edge-IQA 边侧挂载（07.01–07.28）

| 任务 ID | 改进项 | 具体动作 | 验收标准 |
|---------|--------|----------|----------|
| F2-01 | 挂载 scorer | `services/paper1_iqa.py`：`sys.path` 插入 `$PAPER1_ROOT`，`from edge_iqa.scorer import compute_q`（以 paper1 实际 API 为准） | 与 P2-T03 一致：**CPU p95 &lt;30ms** @512×512 |
| F2-02 | 响应 schema | 统一返回：`q_img`, `flags`, `t_iqa_ms`, `image_path`（可选） | 与 LangGraph `TypedDict` 字段一致 |
| F2-03 | 失败样例缓存 | evaluate 可选 `debug=true` 写 `logs/paper1_iqa/` | 供 Fig.3 素材 |
| F2-04 | 单元测试 | `test/test_vision.py`：mock 图像 + 无 PAPER1_ROOT 时降级 | CI 不依赖网盘数据 |

**实现要点**：

- 优先 **子进程** `python -m edge_iqa.cli`（避免 uvicorn 与 rclpy 同进程 GIL 争用）；备选同进程 import。  
- 不在本仓复制 `scorer.py` 源码。

---

### Phase F3：闭环脚本与 M6 辅轨（07.15–08.15）

| 任务 ID | 改进项 | 具体动作 | 验收标准 |
|---------|--------|----------|----------|
| F3-01 | 闭环脚本 | `scripts/paper1_closed_loop.sh`：启动 testall（或复用已启动栈）→ 调用 `doctor/paper1` 的 `langgraph_router` 单次 run | **10 trial** 生成 `run_001.jsonl` |
| F3-02 | 计时规范 | JSONL 每行含：`t_capture`, `t_iqa`, `t_route`, `latency_ms`, `retry_count`, `route_decision`, `q_img` | 与 [论文1_V19.md](./论文1_V19.md) §2.2 State 一致 |
| F3-03 | M6 批量 | `scripts/paper1_run_m6.sh`：50 trial，输出 `experiments/results/franka_m6_rtt.csv` | p50/p95 可画 Fig.S1 |
| F3-04 | franka_bridge | 在 **paper1** 实现 `sim/franka_bridge/client.py`（本仓只提供 API 契约文档） | P3-T03 联调通过 |

**`paper1_closed_loop.sh` 伪代码**：

```bash
export PAPER1_ROOT="${PAPER1_ROOT:-/mnt/e/work/ppt-builder/doctor/paper1}"
export FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000/api/v1}"
export FRANKA_API_KEY="${FRANKA_API_KEY:-franka-api-default-key}"

# 1. 可选：确保 testall 已起
# 2. cd "$PAPER1_ROOT" && python -m langgraph_router.run --trials 10 \
#      --api-base "$FRANKA_API_BASE" --log experiments/logs/run_001.jsonl
```

---

### Phase F4：论文交付与可复现包（08.10–09.30）

| 任务 ID | 改进项 | 具体动作 | 验收标准 |
|---------|--------|----------|----------|
| F4-01 | 复现 README | `docs-zh/paper1/V19/REPRODUCE_franka.md`：从 clone 到 M6 全流程 | 他人可按文档跑通 10 trial |
| F4-02 | Supp. 素材 | 打包 anonymized `run_001.jsonl` 样例（无患者图像） | 随投稿 Supplementary |
| F4-03 | API 版本锁定 | `requirements-paper1.txt` 或文档记录 FastAPI/LangGraph 版本 | 回应 R6（API 变更）风险 |
| F4-04 | 与 CSV 对齐 | M6 汇总脚本只读 JSONL，不写主实验 `main_exp.yaml` | 避免双轨数字混淆 |

---

## 5. 关键接口契约（实现前冻结）

### 5.1 `POST /api/v1/vision/evaluate`

**请求**（二选一）：

- `multipart/form-data`：`file=@image.png`  
- `application/json`：`{ "image_path": "/abs/path.png" }`（仅调试，生产禁绝对外路径）

**响应**：

```json
{
  "q_img": 0.72,
  "flags": ["blur"],
  "t_iqa_ms": 12.4,
  "threshold_tau": 0.55,
  "meta": { "scorer": "edge_iqa", "version": "0.1.0" }
}
```

### 5.2 `POST /api/v1/motion/skills/{skill_name}`

**路径参数**：`skill_name ∈ { go_to_tongue_pose, go_to_face_pose }`（对外名；内部映射 `poses.yaml`）

**响应**：与现有 `MotionTaskResponse` 一致，增加 `t_move_start`, `t_move_end`（可选，供 RTT）。

### 5.3 JSONL 轨迹（单行示例）

```json
{
  "trial_id": 1,
  "image_path": "experiments/debug/capture_001.png",
  "q_img": 0.41,
  "flags": ["blur"],
  "retry_count": 1,
  "route_decision": "resample_edge",
  "t_capture": "2026-07-20T10:00:01.123Z",
  "t_iqa": "2026-07-20T10:00:01.145Z",
  "t_route": "2026-07-20T10:00:01.148Z",
  "latency_ms": 890.2
}
```

---

## 6. 与论文章节 / 指标的映射

| 论文要素 | franka_ros2 贡献 | 主轨/辅轨 |
|----------|------------------|-----------|
| §3.2 Edge gateway | `franka_api_server` + vision 路由 | 叙述 + 演示 |
| §3.3 Device skills | `poses.yaml` + skills API | 辅轨 |
| §4.3 Closed-Loop Protocol | `paper1_closed_loop.sh` + JSONL | 辅轨 |
| §5.5 Qualitative FR3 | 假硬件重拍序列截图 | 辅轨 |
| **M1** RTT p50/p95 | **主**：`run_matrix.py`；**辅**：M6 CSV | 主轨定稿数字 |
| **M6** 50 trials | `paper1_run_m6.sh` | 仅趋势一致 |
| Fig.S1 | 由 M6 CSV 绘制 | Supplementary |

---

## 7. 工程治理与质量

### 7.1 分支与提交约定

- 功能分支：`paper1/f1-skills`、`paper1/f2-vision` 等，便于与 `bot0508` 主开发隔离。  
- 提交信息：`feat(paper1): ...` / `docs(paper1): ...`，可用 `bun run mygit`。  
- **禁止**将 `.env.mygit` 中的密钥写入论文图或公开日志。

### 7.2 测试策略

| 层级 | 内容 |
|------|------|
| API 单测 | `test_vision.py`, skills 路由 |
| 集成 | `scripts/check_paper1_env.sh` + 10 trial JSONL |
| 回归 | `testall.sh` 仍作为非 paper1 基线；paper1 用独立脚本 |

### 7.3 与 `doctor/paper1` 的协作边界

| 归属 paper1 | 归属 franka_ros2 |
|-------------|------------------|
| `edge_iqa/`, `langgraph_router/` | `routers/vision.py`（转发） |
| `experiments/run_matrix.py`, B0–B3 | `scripts/paper1_*.sh` |
| Fig.5–7, Table II | Fig.S1、§5.5 截图 |
| `sim/franka_bridge/client.py` | OpenAPI + ENV.md |

---

## 8. 风险与缓解（franka 侧）

| ID | 风险 | 缓解 |
|----|------|------|
| RF1 | WSL Git/网络推送失败 | 已用 Windows Git；论文数据不依赖 push 频率 |
| RF2 | `PAPER1_ROOT` 未挂载 | `check_paper1_env.sh` 启动前硬失败 |
| RF3 | rclpy 与 FastAPI 同进程不稳定 | IQA 子进程；MoveIt 独立节点 |
| RF4 | Gazebo 相机话题名变更 | launch 参数化 + 文档固定一组 |
| RF5 | 仅有 `move_joints` 难调舌位 | F1 必须完成 poses.yaml + skills |
| RF6 | 辅轨 RTT 与主轨 M1 数值不一致 | 论文明确写「趋势一致」；主轨不给 franka 数字 |

---

## 9. 近期两周优先行动（建议顺序）

| 周 | 优先级 | 行动 | 负责 |
|----|--------|------|------|
| W1 | P0 | 编写 `ENV.md` + `check_paper1_env.sh` | 学生/AI |
| W1 | P0 | `colcon build` + `testall.sh` 通过并记录 | 学生 |
| W1 | P1 | `poses.yaml` + `POST /motion/skills/*` | AI |
| W2 | P1 | `vision.py` 占位 + API 文档 | AI |
| W2 | P1 | `paper1_gazebo_capture.sh` → 首张 PNG | 学生 |
| 并行 | P0 | ppt-builder：TCM-Tongue 全量（与 franka 无关但阻塞主实验） | 学生 |

---

## 10. 文档索引（V19 / franka_ros2）

| 文件 | 用途 |
|------|------|
| [论文1_V19.md](./论文1_V19.md) | 论文完整大纲 |
| [科研规划_论文I_V19.md](./科研规划_论文I_V19.md) | 双仓科研规划 |
| [论文1_V19_tasks.json](./论文1_V19_tasks.json) | 任务 DAG（含 F0–F3） |
| [论文1_V19_AI执行手册.md](./论文1_V19_AI执行手册.md) | AI 分任务提示 |
| [README.md](./README.md) | V19 目录导航（预览无 Mermaid） |
| **本文档** | **franka_ros2 专项优化计划** |
| [AI科研执行总纲_V19.md](./AI科研执行总纲_V19.md) | **AI 主执行**：5 阶段压缩排期、科研成果对齐 |
| [phases/](./phases/) | **各阶段科研安排**（§/Fig/指标 + AI 任务 + 验收） |
| [franka_ros2_技术实现方案.md](./franka_ros2_技术实现方案.md) | 模块设计、API、数据流、文件清单 |
| [franka_ros2_研发任务清单.md](./franka_ros2_研发任务清单.md) | Sprint 文件级对照（已由总纲 supersede） |
| [ENV.md](./ENV.md) | 双仓环境变量 |
| `docs-zh/paper1/V19/REPRODUCE_franka.md` | （待建）M6 复现步骤 |

---

## 11. 验收总表（投稿前 franka_ros2 必达）

- [ ] F0：`PAPER1_ROOT` 可读，`testall.sh` 稳定  
- [ ] F1：`tongue_pose` / `face_pose` 可通过 API 到达  
- [ ] F1：`POST /vision/evaluate` 契约稳定（先占位后挂载 scorer）  
- [ ] F2：边侧 IQA p95 &lt;30ms（与 paper1 P2-T03 一致）  
- [ ] F3：`paper1_closed_loop.sh` 产出 ≥10 行 JSONL  
- [ ] F3：M6 共 50 trial，CSV 可画 Fig.S1  
- [ ] 论文 I 实验未调用 stiffness/collision API  
- [ ] `REPRODUCE_franka.md` 第三方可复现辅轨  

---

*本文档随 `论文1_V19_tasks.json` 中 F0–F3 任务状态更新；算法细节以 `doctor/paper1` 为准。*
