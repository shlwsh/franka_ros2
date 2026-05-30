# franka_ros2 对论文 I 的科研支撑说明

> **文档版本**：V1 | 2026-05-30
> **依据**：[论文 1_V19.md](./paper1/V19/论文1_V19.md)、[franka_ros2 优化改进计划](./paper1/V19/franka_ros2_优化改进计划.md)
> **目标读者**：博士论文评审、论文 I 合作者

---

## 1. 定位总览

论文 I 的核心工作是 **Edge-IQA + Confidence-Aware Routing（LangGraph）** 的云边协同医疗图像采集框架。`franka_ros2` 在该工作中承担**物理执行层（Device + Edge 执行面）**的角色——即 FR3 机械臂的运动控制、相机图像采集，以及边侧 HTTP 网关的 Edge-IQA 转发。

**双仓分工**：

| 仓 | 内容 | 论文角色 |
|----|------|----------|
| `doctor/paper1` | Edge-IQA、LangGraph、实验脚本、主实验数据 | **主实验（M1–M5）** |
| `franka_ros2`（本仓） | FR3 运动 API、Edge-IQA 网关、Skills、闭环脚本 | **辅轨（M6 / §5.5）** |

本仓**不**产出论文主图数据（Fig.5–7, Table II），而是提供：
- §3 系统架构中 Device–Edge 层的可运行原型
- §4.3 闭环协议的可复现 JSONL 轨迹
- §5.5 FR3 假硬件采集序列的定性演示
- M6 辅轨 RTT 趋势（50 trial，与离线 M1 方向一致）

---

## 2. 架构映射

### 2.1 与论文 §3 Cloud–Edge Collaborative Framework 的对应

论文 §3 描述的三层架构中，本仓覆盖 **Device 层 + Edge 执行面**：

```
┌─────────────────────────────────────────────────────────────────┐
│                      Cloud（论文 I 主仓：doctor/paper1）           │
│  vision service / LangGraph / B0–B3 experiments / main metrics   │
└────────────────────────────┬────────────────────────────────────┘
                             │ HTTP / gRPC
┌────────────────────────────▼────────────────────────────────────┐
│               Edge Gateway（franka_api_server 本仓）               │
│  FastAPI (:8000)                                                  │
│  ├── POST /api/v1/vision/evaluate   ← Edge-IQA 转发（子进程调用） │
│  ├── POST /api/v1/motion/skills/*  ← 具名 Skills（tongue/face）  │
│  ├── GET  /api/v1/status/*          ← 机器人状态                  │
│  └── WebSocket /ws                  ← 实时状态推送                │
└────────────────────────────┬────────────────────────────────────┘
                             │ DDS（ROS 2 内部通信）
┌────────────────────────────▼────────────────────────────────────┐
│                    Device（FR3 物理层 本仓）                        │
│  franka_hardware (FCI 1kHz) → ros2_control → MoveIt 2            │
│  franka_gazebo_bringup（仿真辅轨）                               │
│  Camera → capture → PNG → vision/evaluate                        │
└─────────────────────────────────────────────────────────────────┘
```

### 2.2 关键模块对应关系

| 论文 I 要素 | 本仓对应实现 | 文件位置 |
|-------------|-------------|----------|
| Edge gateway（§3.2） | `franka_api_server` FastAPI 应用 | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/app.py` |
| Vision evaluate endpoint | `POST /api/v1/vision/evaluate` | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/routers/vision.py` |
| Edge-IQA 调用（§4.1） | `services/paper1_iqa.py`（子进程调用 `doctor/paper1/edge_iqa`） | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/services/paper1_iqa.py` |
| Device skills（§3.3） | `skills/poses.yaml` + Skills API | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/skills/poses.yaml`、`$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/routers/motion.py` |
| `go_to_tongue_pose` | 7 关节角：`[0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]` | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/skills/poses.yaml` |
| `go_to_face_pose` | 7 关节角：`[0.1, -0.5, 0.05, -2.0, 0.0, 1.4, 0.7]` | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/skills/poses.yaml` |
| ROS 桥接 | `ros_bridge.py`（rclpy 订阅 /joint_states 等） | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/ros_bridge.py` |
| Paper I mode | `PAPER1_MODE=1` 禁用 stiffness/collision 路由 | `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/app.py` |

---

## 3. 核心 API 详解

### 3.1 Vision Evaluate（Edge-IQA 网关）

```bash
POST /api/v1/vision/evaluate
Header: X-API-Key: franka-api-default-key
Content-Type: multipart/form-data  # file=@image.png
# 或
Content-Type: application/json     # {"image_path": "/abs/path.png"}
```

**响应示例**：

```json
{
  "q_img": 0.72,
  "flags": ["blur"],
  "t_iqa_ms": 12.4,
  "threshold_tau": 0.55,
  "meta": { "scorer": "edge_iqa", "mode": "subprocess" }
}
```

**调用链路**：

```
$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/routers/vision.py (FastAPI)
  └─► $FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/services/paper1_iqa.py::evaluate_image_path()
        ├─► 子进程：python -m edge_iqa.cli --image <path> --json
        │     （调用 $FRANKA_ROS2_ROOT/doctor/paper1/edge_iqa/scorer.py）
        └─► 同进程：from edge_iqa.scorer import compute_q（备选）
```

`paper1_iqa.py` 通过 `PAPER1_ROOT` 环境变量定位 `doctor/paper1`。默认 `PAPER1_ROOT` 从本仓根目录向上两级指向 `doctor/paper1`（可通过环境变量覆盖）。

### 3.2 Skills API（具名位姿）

```bash
POST /api/v1/motion/skills/go_to_tongue_pose
Header: X-API-Key: franka-api-default-key
# 内部映射到 joints: [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785]
# 然后调用 ros_bridge.send_ptp_motion()
```

```bash
POST /api/v1/motion/skills/go_to_face_pose
Header: X-API-Key: franka-api-default-key
# 内部映射到 joints: [0.1, -0.5, 0.05, -2.0, 0.0, 1.4, 0.7]
```

### 3.3 Joints Move API

```bash
POST /api/v1/motion/move_joints
{
  "goal_joint_configuration": [0.0, -0.785, 0.0, -2.356, 0.0, 1.571, 0.785],
  "max_velocity_scaling": 0.3,
  "goal_tolerance": 0.02,
  "async_execution": true
}
```

---

## 4. 闭环数据流（辅轨）

一次完整 trial 的数据流如下（对应论文 §4.3 闭环采集协议）：

```
1. capture（LangGraph doctor/paper1 主仓）
   └─► Gazebo 或相机 → /capture_001.png

2. edge_iqa
   └─► POST /api/v1/vision/evaluate (multipart file)
       └─► 返回 { q_img, flags, t_iqa_ms }

3. route（LangGraph 决策）
   └─► if q_img < tau → route_decision = "resample_edge"
       if q_img >= tau → route_decision = "upload_cloud"
       if retry > K → route_decision = "fail_safe"

4. resample_edge（如需重拍）
   └─► POST /api/v1/motion/skills/go_to_tongue_pose
       └─► ros_bridge → MoveIt → FR3 执行

5. JSONL 写盘
   └─► { trial_id, q_img, flags, retry_count, route_decision,
         t_capture, t_iqa, t_route, latency_ms }
```

**JSONL 轨迹字段**（与论文 §2.2 State 一致）：

| 字段 | 说明 |
|------|------|
| `trial_id` | 试验序号 |
| `image_path` | 采集图像路径 |
| `q_img` | Edge-IQA 得分 |
| `flags` | 失败标签 `["blur"]` 或 `[]` |
| `retry_count` | 当前重拍次数 |
| `route_decision` | `resample_edge` \| `upload_cloud` \| `fail_safe` |
| `t_capture` | ISO8601 时间戳 |
| `t_iqa` | ISO8601 时间戳 |
| `t_route` | ISO8601 时间戳 |
| `latency_ms` | capture→route 总延迟（ms） |

---

## 5. 论文指标的支撑关系

| 论文指标 | 支撑方式 | 数据来源 |
|----------|----------|----------|
| **M1** RTT p50/p95 | 主数据来自离线 `run_matrix.py`；辅轨通过 JSONL `latency_ms` 验证趋势一致 | `$FRANKA_ROS2_ROOT/doctor/paper1` 主轨 + 本仓 `$FRANKA_ROS2_ROOT/scripts/paper1_run_m6.sh` |
| **M2** 有效采集率 | 主数据来自主轨；辅轨 10 trial JSONL 验证可行性 | `$FRANKA_ROS2_ROOT/doctor/paper1` 主轨 |
| **M3** 云端无效上传占比 | 主数据来自主轨；辅轨通过 JSONL `route_decision` 分布验证 | `$FRANKA_ROS2_ROOT/doctor/paper1` 主轨 |
| **M4** τ 灵敏度 | 主数据来自主轨 | `$FRANKA_ROS2_ROOT/doctor/paper1` 主轨 |
| **M5** 跨集泛化 | 主数据来自主轨 | `$FRANKA_ROS2_ROOT/doctor/paper1` 主轨 |
| **M6** franka 50 trial RTT | **本仓直接产出**：JSONL → CSV → Fig.S1 | 本仓 `$FRANKA_ROS2_ROOT/scripts/paper1_run_m6.sh` |
| **§5.5** FR3 采集序列 | **本仓直接产出**：截图或视频 | 本仓 Gazebo 或 fake hardware |
| **§4.3** JSONL 轨迹样例 | **本仓直接产出**：可附于 Supplementary | 本仓 `$FRANKA_ROS2_ROOT/scripts/paper1_closed_loop.sh` |

> **重要说明**：论文主图（Fig.5–7, Table II）的所有数字**必须**来自 `doctor/paper1` 的离线矩阵实验。本仓仅产出辅轨（M6、§5.5），其目的是：
> 1. 演示 Edge-IQA + LangGraph 在真实机器人链路上可执行
> 2. 验证离线实验结论在物理系统上的趋势一致性
> 3. 产出可附于 Supplementary 的 JSONL 样例

---

## 6. 关键设计决策说明

### 6.1 为什么 Edge-IQA 不直接内嵌到 franka_hardware？

论文 I 的算法贡献（Edge-IQA、LangGraph Routing）独立于机器人硬件平台，且需要在 `doctor/paper1` 中进行独立实验验证。将 IQA 逻辑放在 `doctor/paper1` 中，通过 HTTP 子进程调用，保持了：
- **算法边界清晰**：主仓负责算法迭代，不受 ROS 包构建约束
- **实验可复现**：离线实验无需启动 ROS 环境
- **部署灵活**：同一 `scorer.py` 可在边侧网关和离线实验中复用

### 6.2 为什么用 Skills API 而非直接调用 move_joints？

论文 §3.3 要求用"具名 Skill"表达采集意图（`go_to_tongue_pose`、`go_to_face_pose`），而非暴露原始关节角。这是因为：
- 具名 Skill 是跨平台的抽象接口（未来可映射到其他机械臂）
- LangGraph 决策层只需知道"去舌位"，无需关心具体关节值
- `$FRANKA_ROS2_ROOT/franka_api_server/franka_api_server/skills/poses.yaml` 作为配置文件，可在不修改代码的情况下调整采集位姿

### 6.3 PAPER1_MODE 的作用

`PAPER1_MODE=1` 时，`franka_api_server` 自动禁用以下路由：
- `POST /api/v1/controller/stiffness`
- `POST /api/v1/controller/collision`

这是因为论文 I 的实验**不使用**阻抗/碰撞控制（属博士论文他章内容），避免实验代码误触影响结果。

---

## 7. 环境变量参考

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `PAPER1_ROOT` | `$FRANKA_ROS2_ROOT/doctor/paper1` | 算法主仓路径 |
| `PAPER1_MODE` | `false` | 设为 `true` 禁用 controller 路由 |
| `PAPER1_IQA_SUBPROCESS` | `true` | 子进程调用 edge_iqa（避免 GIL 争用） |
| `PAPER1_IQA_TIMEOUT_S` | `5.0` | IQA 调用超时 |
| `PAPER1_VISION_THRESHOLD_TAU` | `0.55` | Edge-IQA 阈值 |
| `PAPER1_VISION_PLACEHOLDER_Q` | `0.5` | 无 edge_iqa 时的占位得分 |
| `PAPER1_UPLOAD_DIR` | `$FRANKA_ROS2_ROOT/.cache/paper1_uploads` | 图像上传缓存 |
| `FRANKA_API_KEY` | `franka-api-default-key` | API 认证密钥 |
| `FRANKA_API_HOST` | `0.0.0.0` | API 监听地址 |
| `FRANKA_API_PORT` | `8000` | API 监听端口 |

完整环境配置见 [docs-zh/paper1/V19/ENV.md](./paper1/V19/ENV.md)。

---

## 8. 快速验收检查清单

以下为本仓对论文 I 的最低验收标准：

- [ ] `PAPER1_ROOT` 路径可读，`$FRANKA_ROS2_ROOT/doctor/paper1/edge_iqa` 目录存在
- [ ] `colcon build` + `bash $FRANKA_ROS2_ROOT/scripts/testall.sh` 稳定通过
- [ ] `POST /api/v1/motion/skills/go_to_tongue_pose` 返回 200（MoveIt fake HW）
- [ ] `POST /api/v1/vision/evaluate`（附图片）返回 `{ q_img, flags, t_iqa_ms }`
- [ ] `PAPER1_MODE=1` 启动后日志显示 "controller routes disabled"
- [ ] `bash $FRANKA_ROS2_ROOT/scripts/paper1_closed_loop.sh` 产出 ≥10 行 JSONL
- [ ] JSONL 每行包含 `q_img`、`route_decision`、`latency_ms` 字段
- [ ] 50 trial M6 脚本可产出 CSV，p50/p95 趋势与离线 M1 一致
- [ ] 论文实验代码**未调用** stiffness/collision API

---

## 9. 文档索引

| 文档 | 说明 |
|------|------|
| [论文 1_V19.md](./paper1/V19/论文1_V19.md) | 论文完整大纲 |
| [franka_ros2_优化改进计划](./paper1/V19/franka_ros2_优化改进计划.md) | F0–F4 研发任务清单 |
| [科研规划_论文I_V19.md](./paper1/V19/科研规划_论文I_V19.md) | 双仓科研规划 |
| [ENV.md](./paper1/V19/ENV.md) | 环境变量完整配置 |
| [REPRODUCE_franka.md](./paper1/V19/REPRODUCE_franka.md)（待建） | 第三方复现步骤 |

---

*本文档随论文 I 进展同步更新；工程实现细节以本仓代码为准。*
