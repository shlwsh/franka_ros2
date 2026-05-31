# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# franka_ros2 — Project Overview

Franka Robotics research robot ROS 2 (Humble) integration via Franka Control Interface (FCI) at 1kHz. Supports FR3, Panda arms, and TMR mobile robots.

- **Languages**: C++ (C++17 / C++20) + Python (franka_api_server, franka_bringup)
- **Frameworks**: ROS 2 Humble, ros2_control, MoveIt 2
- **License**: Apache 2.0
- **Repo**: https://github.com/frankarobotics/franka_ros2

## 交互语言

中文。文档输出默认写入 `docs-zh/` 目录。

## Directory Structure

```
franka_ros2/
├── franka_hardware/             # C++20 - ros2_control SystemInterface (FCI UDP)
├── franka_example_controllers/  # C++17 - 12 example controllers + PTP node
├── franka_semantic_components/  # C++17 - semantic components (joint/Cartesian state)
├── franka_robot_state_broadcaster/ # C++17 - 1kHz state broadcaster
├── franka_msgs/                 # msg/action/srv definitions
├── franka_gripper/              # C++/Python - Franka Hand gripper
├── franka_bringup/              # Python - launch files and YAML config
├── franka_fr3_moveit_config/    # MoveIt 2 config
├── franka_gazebo_bringup/       # Gazebo simulation launch
├── franka_mobile/               # C++ - TMR v0.2 mobile base (SwerveDriveController)
├── franka_mobile_sensors/       # camera/LIDAR (ignored by COLCON_IGNORE by default)
├── franka_api_server/           # Python FastAPI - REST/WebSocket API + Paper I 边侧网关
├── franka_jazzy_compat/         # ROS 2 Jazzy compatibility headers
├── franka_ros2/                 # metapackage
├── src/                         # external dependencies
│   ├── libfranka/              # C++ robot communication library
│   ├── libfranka-common/       # libfranka common utilities
│   └── franka_description/     # URDF/xacro robot description
├── docs/ docs-zh/              # English/Chinese documentation
├── scripts/                    # helper scripts (testall.sh, start.sh, startapi.sh, etc.)
├── doctor/paper1/              # 论文 I 算法主仓（Edge-IQA + LangGraph，与本仓同仓）
├── dependency.repos            # 外部依赖 VCS 清单（libfranka 0.20.4, franka_description 2.7.0）
├── .cursorrules                # 中文交互规则
├── .clang-format               # Chromium style (C++11, 100 cols)
├── .clang-tidy                 # C++ linting rules
├── AGENTS.md                   # 开发指南（中文，测试、提交约定）
└── pyproject.toml              # Python ruff config (99 cols, single quotes)
```

## Development Commands

### Clone Dependencies

```bash
vcs import src < dependency.repos --recursive --skip-existing
rosdep install --from-paths src --ignore-src --rosdistro humble -y
```

### Build

```bash
# Standard build (--symlink-install allows code edits to take effect immediately)
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF

# Build with tests
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=ON

# Build with clang-tidy checks (CI level)
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DCHECK_TIDY=ON

# Build a specific package only
colcon build --packages-select <package_name> --symlink-install
```

### Test

```bash
colcon test
colcon test-result --all --verbose
colcon test --packages-select <package_name> --event-handlers console_direct+
```

### Local Helper Scripts

```bash
source /opt/ros/<distro>/setup.bash && source install/setup.bash

ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true   # MoveIt fake HW
bash scripts/start.sh    # fake hardware + MoveIt
bash scripts/startapi.sh # API server
bash scripts/testall.sh  # 联合测试（MoveIt fake HW + API）
```

### Docker

```bash
docker compose build
docker compose up -d
docker exec -it franka_ros2 /bin/bash
# Inside container
vcs import src < dependency.repos --recursive --skip-existing
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release
source install/setup.bash
```

### Environment

```bash
source install/setup.sh    # bash
source install/setup.bash  # bash (explicit)
```

## Architecture Overview

```
User Layer
  MoveIt 2 / REST API (HTTP/WebSocket) / rviz2 / keyboard / Xbox

Communication Layer
  franka_api_server (FastAPI + uvicorn) / franka_bringup (launch)

Controller Layer (ros2_control)
  franka_example_controllers (12 controllers)
  franka_robot_state_broadcaster / SwerveDriveController

Semantic Component Layer
  franka_semantic_components: FrankaRobotState, CartesianVelocity

Hardware Abstraction Layer (ros2_control SystemInterface)
  franka_hardware / FrankaHardwareInterface
    UDP (FCI, 1kHz)
  libfranka -> real robot
```

## Core Modules

### franka_hardware (C++20)

`FrankaHardwareInterface` implements `hardware_interface::SystemInterface`, communicating at 1kHz via FCI UDP. Core classes:

- **`Robot`** - wraps `franka::Robot`, manages connections, active control mode switching, low-pass filtering, rate limiting
- **`Model`** - wraps `franka::Model` (mass matrix, Jacobian, gravity vector, Coriolis forces)
- **`FrankaParamServiceServer`** - parameter service (stiffness, end-effector load, TCP frame, collision behavior)
- **`FrankaExecutor`** - rclcpp executor

Supported control interfaces (`robot_type` param: `fr3` or `panda`):

| Control Interface | Description |
|-------------------|-------------|
| `effort` | joint torque control |
| `joint_position` | joint position control |
| `joint_velocity` | joint velocity control |
| `cartesian_velocity` | Cartesian velocity control |
| `cartesian_velocity_with_elbow` | Cartesian velocity + elbow control |
| `cartesian_pose` | Cartesian position control |
| `cartesian_pose_with_elbow` | Cartesian position + elbow control |

### franka_example_controllers (C++17)

12 ros2_control controllers registered via pluginlib to `controller_interface`. All support namespaced deployment (multi-robot scenarios):

`CartesianElbow`, `CartesianOrientation`, `CartesianPose`, `CartesianVelocity`, `Elbow`, `GravityCompensation`, `Gripper`, `JointImpedance`, `JointImpedanceWithIK`, `JointPosition`, `JointVelocity`, `Model`

Executable: `ptp_motion_example_node` - asynchronous PTP motion using MoveIt 2.

### franka_semantic_components (C++17)

- **`FrankaRobotState`** - complete robot state, parses URDF for end-effector link index
- **`FrankaRobotModel`** - kinematics/dynamics model
- **`FrankaCartesianVelocityInterface`** / **`FrankaCartesianPoseInterface`**

### franka_robot_state_broadcaster (C++17)

Publishes `franka_msgs/FrankaRobotState` at full 1kHz. Convenience topics configurable via parameters. Uses `generate_parameter_library`.

### franka_api_server (Python FastAPI)

- **Framework**: FastAPI + uvicorn + pydantic v2
- **Launch**: `ros2 run franka_api_server api_server`
- **Config env vars**: `FRANKA_API_HOST`, `FRANKA_API_PORT`, `FRANKA_API_KEY`, `FRANKA_API_WS_PUBLISH_RATE`

Paper I 专用环境变量（见 `docs-zh/paper1/V19/ENV.md`）：

| 环境变量 | 默认值 | 说明 |
|----------|--------|------|
| `PAPER1_MODE` | false | 禁用 stiffness/collision 路由 |
| `PAPER1_ROOT` | `../doctor/paper1` | 算法主仓路径 |
| `PAPER1_IQA_SUBPROCESS` | true | IQA 子进程调用 |
| `PAPER1_VISION_THRESHOLD_TAU` | 0.55 | Edge-IQA 阈值 |
| `PAPER1_UPLOAD_DIR` | `.cache/paper1_uploads` | 上传图像缓存 |

API 路由：

| 路由 | 方法 | 说明 |
|------|------|------|
| `/api/v1/status/joints` | GET | 关节状态 |
| `/api/v1/status/robot` | GET | 机器人状态 |
| `/api/v1/motion/move_joints` | POST | 关节空间 PTP |
| `/api/v1/motion/skills/{name}` | POST | **Paper I Skills**：`go_to_tongue_pose` / `go_to_face_pose` |
| `/api/v1/motion/skills` | GET | 列出可用 Skills |
| `/api/v1/motion/error_recovery` | POST | 错误恢复 |
| `/api/v1/vision/evaluate` | POST | **Paper I Edge-IQA**：图像质量评估 |
| `/api/v1/gripper/*` | POST | 夹爪控制 |
| `/ws` | WebSocket | 实时状态推送 |
| `/` | 静态 | Dashboard HTML |

核心实现：
- `routers/vision.py` — Edge-IQA 网关，调用 `services/paper1_iqa.py`
- `routers/motion.py` — 运动 + Skills API
- `services/paper1_iqa.py` — 通过子进程或 import 调用 `doctor/paper1/edge_iqa`
- `services/skills_loader.py` — 从 `skills/poses.yaml` 加载具名位姿
- `skills/poses.yaml` — `tongue_pose` / `face_pose` 预定义关节角

### franka_mobile (C++, TMR v0.2)

`SwerveDriveController` implements Ackermann-style differential drive, using `diff_drive_controller` + `kdl_parser` + `generate_parameter_library`. Config in `franka_mobile/config/`.

### Message Definitions (franka_msgs)

| Type | Names |
|------|-------|
| msg | CollisionIndicators, Elbow, Errors, FrankaRobotState, GraspEpsilon, TargetStatus |
| action | ErrorRecovery, Grasp, Homing, Move, PTPMotion |
| srv | SetCartesianStiffness, SetTCPFrame, SetForceTorqueCollisionBehavior, SetFullCollisionBehavior, SetJointStiffness, SetStiffnessFrame, SetLoad |

`franka_msgs/FrankaRobotState` is the core state message, published at 1kHz, containing full joint state, end-effector state, robot errors, and more.

## Launch Files

```bash
# MoveIt + fake hardware (no real robot needed)
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true

# Run an example controller (configure robot IP in franka.config.yaml first)
ros2 launch franka_bringup example.launch.py controller_name:=<controller_name>

# Multi-robot, multi-controller
ros2 launch franka_bringup example.launch.py controller_names:="ctrl1,ctrl2,ctrl3"

# TMR mobile robot - Xbox controller
ros2 launch franka_bringup mobile_teleop.launch.py

# TMR mobile robot - keyboard control
ros2 launch franka_bringup example.launch.py controller_names:="swerve_drive_controller" robot_config_file:="tmr.config.yaml"

# Gazebo simulation
ros2 launch franka_gazebo_bringup gazebo_franka_arm_example_controller.launch.py

# API server
ros2 launch franka_api_server api_server.launch.py
```

## Code Standards

### C++

- **Style**: .clang-format - Chromium, C++11, 100 cols, SortIncludes: true
- **Linting**: .clang-tidy - HeaderFilter: ^franka_.*
- **Naming**: Namespace lower_case, Class CamelCase, Function camelBack, variable lower_case, kConstant CamelCase
- **Disabled**: vararg, array-to-pointer-decay, deprecated-declarations
- **C++ version**: franka_hardware uses C++20; all other C++ packages use C++17

### Python

- **Tool**: ruff (pyproject.toml)
- **Line length**: 99, single quotes, no type-based ordering
- **Import order**: stdlib | third-party (no first-party distinction; all non-stdlib packages sorted alphabetically)

### Commits

- DCO sign-off required (Signed-off-by: ...)
- CI includes clang-tidy checks
- 推荐简短发件式前缀：`fix: ...`、`chore: ...`、`feat(paper1): ...`

## Important Config Files

| File | Purpose |
|------|---------|
| franka_bringup/config/franka.config.yaml | robot IP, namespace, robot_type (fr3/panda), controller selection |
| franka_bringup/config/controllers.yaml | controller_manager config (update_rate: 1000Hz, thread_priority: 98) |
| franka_bringup/config/tmr.config.yaml | TMR mobile robot config |
| franka_api_server/config/api_server.yaml | API server config |
| franka_api_server/franka_api_server/skills/poses.yaml | Paper I 具名位姿定义 |
| dependency.repos | external VCS deps (libfranka 0.20.4, franka_description 2.7.0) |
| limits.conf | real-time kernel limits (rtprio 99, memlock unlimited) |

## CI/CD

- **CI** (.github/workflows/ci.yml): Ubuntu latest container, build + test + clang-tidy
- **Release** (.github/workflows/release.yml): git tag triggered, extracts version notes from CHANGELOG.rst
- **Jenkinsfile**: additional CI config

## Documentation

- **English**: README.md, docs/
- **Chinese**: docs-zh/（快速入门、安装指南、MoveIt 研究等）
- **Paper I 专项**: docs-zh/paper1/V19/（论文大纲、科研规划、技术方案）
- **Per-package**: */doc/index.rst or */README.md
- **Official**: https://frankarobotics.github.io/docs

## Known Limitations

- franka_ros2 is in rapid development; breaking changes are expected
- franka_mobile_sensors is ignored by COLCON_IGNORE by default; delete that file to enable it
- libfranka UDP requires a real-time kernel; Docker Desktop is not recommended (use Docker Engine)
- CI 基于 ROS 2 Humble；本地脚本当前默认加载 ROS 2 Jazzy

<!-- gitnexus:start -->
# GitNexus — Code Intelligence

This project is indexed by GitNexus as **franka_ros2** (6730 symbols, 9807 relationships, 159 execution flows). Use the GitNexus MCP tools to understand code, assess impact, and navigate safely.

> If any GitNexus tool warns the index is stale, run `npx gitnexus analyze` in terminal first.

## Always Do

- **MUST run impact analysis before editing any symbol.** Before modifying a function, class, or method, run `gitnexus_impact({target: "symbolName", direction: "upstream"})` and report the blast radius (direct callers, affected processes, risk level) to the user.
- **MUST run `gitnexus_detect_changes()` before committing** to verify your changes only affect expected symbols and execution flows.
- **MUST warn the user** if impact analysis returns HIGH or CRITICAL risk before proceeding with edits.
- When exploring unfamiliar code, use `gitnexus_query({query: "concept"})` to find execution flows instead of grepping. It returns process-grouped results ranked by relevance.
- When you need full context on a specific symbol — callers, callees, which execution flows it participates in — use `gitnexus_context({name: "symbolName"})`.

## Never Do

- NEVER edit a function, class, or method without first running `gitnexus_impact` on it.
- NEVER ignore HIGH or CRITICAL risk warnings from impact analysis.
- NEVER rename symbols with find-and-replace — use `gitnexus_rename` which understands the call graph.
- NEVER commit changes without running `gitnexus_detect_changes()` to check affected scope.

## Resources

| Resource | Use for |
|----------|---------|
| `gitnexus://repo/franka_ros2/context` | Codebase overview, check index freshness |
| `gitnexus://repo/franka_ros2/clusters` | All functional areas |
| `gitnexus://repo/franka_ros2/processes` | All execution flows |
| `gitnexus://repo/franka_ros2/process/{name}` | Step-by-step execution trace |

## CLI

| Task | Read this skill file |
|------|---------------------|
| Understand architecture / "How does X work?" | `.claude/skills/gitnexus/gitnexus-exploring/SKILL.md` |
| Blast radius / "What breaks if I change X?" | `.claude/skills/gitnexus/gitnexus-impact-analysis/SKILL.md` |
| Trace bugs / "Why is X failing?" | `.claude/skills/gitnexus/gitnexus-debugging/SKILL.md` |
| Rename / extract / split / refactor | `.claude/skills/gitnexus/gitnexus-refactoring/SKILL.md` |
| Tools, resources, schema reference | `.claude/skills/gitnexus/gitnexus-guide/SKILL.md` |
| Index, status, clean, wiki CLI commands | `.claude/skills/gitnexus/gitnexus-cli/SKILL.md` |

<!-- gitnexus:end -->
