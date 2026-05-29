# franka_ros2 论文 I 辅轨 — 技术实现方案

> **版本**：V19-tech-1 | 2026-05-29  
> **上游**：[franka_ros2_优化改进计划.md](./franka_ros2_优化改进计划.md)  
> **关联**：[论文1_V19_tasks.json](./论文1_V19_tasks.json)、[ENV.md](./ENV.md)  
> **目标读者**：研发执行（学生 / AI Agent），可直接按文件清单改代码

---

## 1. 范围与不变量

### 1.1 本仓交付边界

| 交付 | 不交付 |
|------|--------|
| FastAPI 边网关扩展（vision、skills） | `edge_iqa/`、`langgraph_router/` 源码 |
| `scripts/paper1_*.sh` 闭环与 M6 | 主实验 M1–M3 数字（`run_matrix.py`） |
| OpenAPI / ENV / 复现文档 | K8s、真机大规模实验、mobile 导航 |
| 调用 `PAPER1_ROOT` 的 IQA 桥接 | 在 ROS 包内复制 scorer |

### 1.2 工程不变量（实现时必须检查）

1. **`PAPER1_MODE=1`** 时不注册 `routers/controller.py`（刚度/碰撞端点对论文 I 禁用）。
2. **IQA 默认子进程**，避免 uvicorn + rclpy 同进程 GIL 争用（RF3）。
3. **`poses.yaml` 仅关节空间**，复用现有 `move_joints` → `ros_bridge.send_ptp_motion`。
4. **JSONL 字段名**与 `doctor/paper1` 的 LangGraph `TypedDict` 一致，不在本仓改语义。
5. **调试 `image_path`** 仅接受 `PAPER1_ROOT` 下路径或 API 上传临时目录，禁止任意绝对路径（生产）。

---

## 2. 目标目录与模块划分

```
franka_api_server/franka_api_server/
├── app.py                      # 改：条件注册 controller / vision
├── config.py                   # 改：PAPER1_MODE, PAPER1_ROOT, IQA 子进程开关
├── routers/
│   ├── motion.py               # 改：skills 路由
│   └── vision.py               # 新
├── models/
│   ├── motion.py               # 改：SkillMotionResponse 可选时间戳
│   └── vision.py               # 新
├── services/
│   ├── __init__.py             # 新
│   ├── skills_loader.py        # 新：读 poses.yaml
│   └── paper1_iqa.py           # 新：子进程 / import scorer
└── skills/
    └── poses.yaml              # 新

franka_api_server/test/
├── test_api.py                 # 改：skills 冒烟
└── test_vision.py              # 新

scripts/
├── check_paper1_env.sh         # 已有，随功能增补检查项
├── paper1_gazebo_capture.sh    # 新
├── paper1_closed_loop.sh       # 新
└── paper1_run_m6.sh            # 新

docs-zh/paper1/V19/
├── ENV.md                      # 已有
├── REPRODUCE_franka.md         # F4 新建
└── API_CONTRACT_paper1.md        # 可选：从本文 §5 抽出冻结契约
```

---

## 3. 分模块技术设计

### 3.1 F0 — 环境与论文模式

#### 3.1.1 `config.py` 扩展

```python
# 新增字段（环境变量优先）
paper1_mode: bool          # PAPER1_MODE=1
paper1_root: str           # PAPER1_ROOT，默认 <franka_ros2>/doctor/paper1
iqa_subprocess: bool       # PAPER1_IQA_SUBPROCESS=1（默认 true）
iqa_timeout_s: float       # 默认 5.0
paper1_upload_dir: str     # 临时图像，默认 $FRANKA_ROS2_ROOT/.cache/paper1_uploads
```

#### 3.1.2 `app.py` 条件路由

```python
from .config import settings
# ...
if not settings.paper1_mode:
    app.include_router(controller.router, prefix="/api/v1")
app.include_router(vision.router, prefix="/api/v1")  # F1 起始终存在
```

启动日志打印：`PAPER1_MODE=1, controller routes disabled`。

#### 3.1.3 `check_paper1_env.sh` 增补（随阶段）

| 阶段 | 新增检查 |
|------|----------|
| F1 后 | `poses.yaml` 存在；`curl POST .../motion/skills/go_to_tongue_pose` |
| F2 后 | `vision.py` 存在；无 PAPER1_ROOT 时占位模式 |
| F3 后 | `paper1_closed_loop.sh` 可执行 |

---

### 3.2 F1 — Skills 与 Vision 占位

#### 3.2.1 `skills/poses.yaml`  schema

```yaml
version: "0.1.0"
robot_type: fr3
poses:
  tongue_pose:
    description: "舌诊采集预定义关节角（fake HW 标定）"
    joint_positions: [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]  # rad, 7-DOF
    goal_tolerance: 0.02
    max_velocity_scaling: 0.3
  face_pose:
    description: "面诊/重拍预定义关节角"
    joint_positions: [0.1, -0.5, 0.05, -2.0, 0.0, 1.4, 0.7]
    goal_tolerance: 0.02
    max_velocity_scaling: 0.3
```

**标定流程**：在 MoveIt fake HW 下用 RViz 交互调角 → 写入 yaml → `POST /motion/skills/go_to_tongue_pose` 两次往返验证 `joint_states` 误差 &lt; `goal_tolerance`。

**路径映射**（对外 API 名 → yaml key）：

| `skill_name`（URL） | yaml key |
|---------------------|----------|
| `go_to_tongue_pose` | `tongue_pose` |
| `go_to_face_pose` | `face_pose` |

#### 3.2.2 `services/skills_loader.py`

- 使用 `importlib.resources` 或 `ament_index` 定位包内 `skills/poses.yaml`。
- `load_pose(skill_name: str) -> MoveJointsRequest`：校验 7 维关节、合并默认速度。
- 未知 skill → `HTTP 404` + `detail="unknown skill"`。

#### 3.2.3 `routers/motion.py` 新增端点

```python
@router.post("/motion/skills/{skill_name}", response_model=MotionTaskResponse)
async def execute_skill(skill_name: str, api_key: str = Depends(get_api_key)):
    req = skills_loader.load_pose(skill_name)
    t0 = time.perf_counter()
    success, msg = await bridge.send_ptp_motion(req)
    t1 = time.perf_counter()
    # 可选：response 增加 t_move_start/end ISO8601（扩展 MotionTaskResponse）
```

与现有 `move_joints` **共用** `ros_bridge.send_ptp_motion`，不新增 ROS Action 类型。

#### 3.2.4 `routers/vision.py`（F1 占位 → F2 实装）

**F1 占位逻辑**：

```python
@router.post("/vision/evaluate", response_model=VisionEvaluateResponse)
async def evaluate_vision(
    file: UploadFile | None = None,
    body: VisionEvaluateRequest | None = None,
    debug: bool = False,
    api_key: str = Depends(get_api_key),
):
    # 解析图像 → 临时路径
    # F1: 固定返回 q_img=0.5, flags=[], t_iqa_ms=0.1
    # F2: 委托 paper1_iqa.run_scorer(path)
```

**请求解析优先级**：

1. `multipart/form-data` 字段 `file`
2. JSON `image_path`（仅当 `path.startswith(paper1_root)` 或位于 `paper1_upload_dir`）

#### 3.2.5 `models/vision.py`

```python
class VisionEvaluateResponse(BaseModel):
    q_img: float
    flags: list[str]
    t_iqa_ms: float
    threshold_tau: float = 0.55
    meta: dict[str, str] = Field(default_factory=dict)

class VisionEvaluateRequest(BaseModel):
    image_path: str | None = None
```

#### 3.2.6 `scripts/paper1_gazebo_capture.sh`

**流程**：

1. `source install/setup.bash`
2. 后台启动 Gazebo launch（`franka_gazebo_bringup`，参数化相机 topic，默认文档化一组）
3. `ros2 run` 或 `python3` 小脚本：`subscribe` → 单帧 → `$PAPER1_ROOT/experiments/debug/capture_001.png`
4. 打印 PNG 路径供 P1-T03 验收

**依赖**：`gzstart.sh` 可复用部分逻辑；相机 topic 写入 `docs-zh/paper1/V19/ENV.md` 固定表。

---

### 3.3 F2 — Edge-IQA 边侧挂载

#### 3.3.1 `services/paper1_iqa.py` 接口

```python
def evaluate_image(image_path: Path, *, debug: bool = False) -> VisionEvaluateResponse:
    """统一入口：子进程或同进程 import。"""
```

#### 3.3.2 子进程方案（推荐）

```bash
python -m edge_iqa.cli --image "$path" --json
```

- `subprocess.run(..., timeout=iqa_timeout_s, capture_output=True)`
- 解析 stdout JSON → `VisionEvaluateResponse`
- CLI 由 **paper1** 实现（F2 联调前可在 paper1 加最小 `edge_iqa/cli.py`）

#### 3.3.3 同进程备选

```python
sys.path.insert(0, settings.paper1_root)
from edge_iqa.scorer import compute_q  # 以 paper1 实际 API 为准
```

仅当子进程不可用且 CI 明确标记时使用。

#### 3.3.4 降级策略（CI / 无挂载）

| 条件 | 行为 |
|------|------|
| `PAPER1_ROOT` 不存在 | `meta.scorer="placeholder"`, `q_img=0.5` |
| import 失败 | HTTP 503 + 日志；单测 mock |
| 超时 | HTTP 504 |

#### 3.3.5 `debug=true`

将输入图复制到 `logs/paper1_iqa/{uuid}.png`（相对 franka_ros2 根或 configurable），供 Fig.3 素材；**禁止**写入公开 git。

#### 3.3.6 性能验收

- 与 P2-T03 对齐：512×512，CPU **p95 &lt; 30ms**
- 在本仓加 `scripts/paper1_iqa_bench.sh`：循环调用 API 100 次，输出 `experiments/results/iqa_api_latency.json`

---

### 3.4 F3 — 闭环脚本与 M6

#### 3.4.1 职责 split

| 组件 | 仓库 | 职责 |
|------|------|------|
| `langgraph_router/run.py` | paper1 | 单次 trial 状态机、capture→iqa→route→resample |
| `sim/franka_bridge/client.py` | paper1 | HTTP 封装：evaluate、skills、计时 |
| `paper1_closed_loop.sh` | franka_ros2 | 启停栈、环境变量、调用 paper1 |
| `paper1_run_m6.sh` | franka_ros2 | 50 trial + CSV 汇总 |

#### 3.4.2 `sim/franka_bridge/client.py`（paper1，契约由本仓文档冻结）

```python
class FrankaApiClient:
    def __init__(self, base: str, api_key: str): ...
    def evaluate(self, image_path: Path) -> dict: ...      # POST /vision/evaluate
    def go_to_skill(self, name: str) -> dict: ...         # POST /motion/skills/{name}
    def capture_from_gazebo(self) -> Path: ...            # 或读已有 PNG
```

本仓提供 **`docs-zh/paper1/V19/API_CONTRACT_paper1.md`**（可从优化计划 §5 复制）供 paper1 实现。

#### 3.4.3 JSONL 写入（paper1 侧，字段本仓脚本只读）

单行 schema（与论文 §2.2 一致）：

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

**计时约定**：

- `t_*`：ISO 8601 UTC，`datetime.now(timezone.utc).isoformat()`
- `latency_ms`：从 `t_capture` 到 motion 完成或 route 结束（paper1 统一定义，写入 README）

#### 3.4.4 `scripts/paper1_closed_loop.sh`

```bash
#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
source "$ROOT/install/setup.bash" 2>/dev/null || true

export PAPER1_ROOT="${PAPER1_ROOT:-/root/work/franka_ros2/doctor/paper1}"
export FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000/api/v1}"
export FRANKA_API_KEY="${FRANKA_API_KEY:-franka-api-default-key}"
export PAPER1_MODE=1

# 1. bash scripts/check_paper1_env.sh
# 2. 若 API 未起：可选启动 testall.sh 后台
# 3. cd "$PAPER1_ROOT" && python -m langgraph_router.run \
#      --trials "${TRIALS:-10}" \
#      --api-base "$FRANKA_API_BASE" \
#      --log "${LOG_PATH:-$PAPER1_ROOT/experiments/logs/run_001.jsonl}"
```

#### 3.4.5 `scripts/paper1_run_m6.sh`

- `TRIALS=50`，输出 `$PAPER1_ROOT/experiments/results/franka_m6_rtt.csv`
- CSV 列建议：`trial_id,latency_ms,t_iqa_ms,route_decision,retry_count,q_img`
- 汇总脚本 **只读 JSONL**，不修改 `main_exp.yaml`（F4-04）

---

### 3.5 F4 — 可复现与交付

| 交付物 | 内容 |
|--------|------|
| `REPRODUCE_franka.md` | clone → rosdep → colcon → testall → 10 trial → M6 |
| `requirements-paper1.txt` | pin: fastapi, uvicorn, httpx, pydantic |
| 样例 JSONL | 脱敏 `run_001.sample.jsonl` 入 `docs-zh/paper1/V19/samples/` |

---

## 4. 数据流与时序

### 4.1 单次 trial（辅轨）

| 步骤 | 组件 | 动作 |
|------|------|------|
| 1 | langgraph_router (paper1) | 调用 `franka_bridge.capture_image()` |
| 2 | franka_bridge → API | `POST /vision/evaluate` |
| 3 | franka_api_server | `paper1_iqa` 子进程评分 |
| 4 | API → bridge | 返回 `q_img`, `flags`, `t_iqa_ms` |
| 5 | LangGraph | `route(q_img, tau, K)` |
| 6a | 若 `resample_edge` | `POST /motion/skills/go_to_tongue_pose` → `send_ptp_motion` |
| 6b | 若 `upload_cloud` | 上传云侧（stub） |
| 7 | LangGraph | `append JSONL line` |

```
LangGraph ──capture──► franka_bridge ──POST /vision/evaluate──► API ──subprocess──► edge_iqa
    │                              ◄── q_img, flags, t_iqa_ms ──┘
    ├── route ── resample ──► POST /motion/skills/... ──► ros_bridge ──► MoveIt
    └── append JSONL
```

### 4.2 部署拓扑（开发机）

```
WSL: franka_ros2
  ├── ros2 launch (fake HW / Gazebo)
  ├── franka_api_server :8000  (PAPER1_MODE=1)
  └── doctor/paper1/（本仓库）
        ├── edge_iqa/
        └── langgraph_router/
```

---

## 5. API 契约（冻结）

与 [franka_ros2_优化改进计划.md](./franka_ros2_优化改进计划.md) §5 相同，实现前 **不得** 擅自改名：

- `POST /api/v1/vision/evaluate`
- `POST /api/v1/motion/skills/{skill_name}`，`skill_name ∈ {go_to_tongue_pose, go_to_face_pose}`
- JSONL 字段：`trial_id`, `q_img`, `flags`, `retry_count`, `route_decision`, `t_capture`, `t_iqa`, `t_route`, `latency_ms`

OpenAPI 更新路径：`franka_api_server/docs-api/api_specification.md`。

---

## 6. 测试策略

| 层级 | 文件 | 内容 |
|------|------|------|
| 单元 | `test_vision.py` | 占位响应、路径校验、mock subprocess |
| 单元 | `test_api.py` | skills 404、合法 skill 返回 200 |
| 集成 | `check_paper1_env.sh` | 双仓路径 + API |
| 集成 | `paper1_closed_loop.sh` | 10 行 JSONL |
| 性能 | `paper1_iqa_bench.sh` | p95 &lt; 30ms |
| 回归 | `testall.sh` | 非 paper1 基线不退化 |

**CI 注意**：`PAPER1_ROOT` 不存在时 vision 走占位，不 fail build。

---

## 7. 与 paper1 任务依赖图（franka 视角）

```
F0-01 ENV ──► F0-02 testall ──► F1-01 poses ──► F1-02 skills API
                    │                │
                    └──────► F1-03 vision 占位 ──► F2-01 scorer 挂载
                    │                │
                    └──────► F1-05 gazebo capture
                                         │
P3-T01/T02 (paper1) ◄── F2-02 schema ──┤
         │                               │
         └──► P3-T03 franka_bridge ──► F3-01 closed_loop ──► F3-03 M6
```

**阻塞关系**：

- F2-01 依赖 paper1 **P2-T01**（scorer 存在）
- F3-01 依赖 paper1 **P3-T03** + 本仓 **F1-01**
- M6 趋势图依赖 F3 全套 + 50 trial 稳定栈

---

## 8. 风险与技术对策

| ID | 对策摘要 |
|----|----------|
| RF2 | `check_paper1_env.sh` 缺目录则 exit 1 |
| RF3 | IQA 子进程；MoveIt 独立 launch |
| RF4 | Gazebo topic 写入 ENV.md + launch 参数 `camera_topic` |
| RF5 | poses 必须经 RViz 标定后入库 |
| RF6 | M6 CSV 与 M1 分文件命名，`franka_m6_*` 前缀 |

---

## 9. 实现顺序（研发入口）

1. **F0**：`config.py` + `app.py` 论文模式；完善 `check_paper1_env.sh`
2. **F1**：`poses.yaml` → `skills_loader` → motion skills 路由 → `vision.py` 占位 → pytest
3. **F1 并行**：`paper1_gazebo_capture.sh`
4. **F2**：`paper1_iqa.py` + 与 paper1 联调 P2-T03
5. **F3**：等 paper1 `franka_bridge` + `langgraph_router.run` 就绪后接脚本
6. **F4**：`REPRODUCE_franka.md` + 样例 JSONL

---

*下一文档：[franka_ros2_研发任务清单.md](./franka_ros2_研发任务清单.md) — 可勾选任务、工时与负责人。*
