# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

# franka_ros2 — Project Overview

Franka Robotics research robot ROS 2 (Humble) integration via Franka Control Interface (FCI) at 1kHz. Supports FR3, Panda arms, and TMR mobile robots.

- **Languages**: C++ (C++17 / C++20) + Python (franka_api_server, franka_bringup)
- **Frameworks**: ROS 2 Humble, ros2_control, MoveIt 2
- **License**: Apache 2.0
- **Repo**: https://github.com/frankarobotics/franka_ros2

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
├── franka_api_server/           # Python FastAPI - REST/WebSocket API
├── franka_jazzy_compat/         # ROS 2 Jazzy compatibility headers
├── franka_ros2/                 # metapackage
├── src/                         # external dependencies
│   ├── libfranka/              # C++ robot communication library
│   ├── libfranka-common/       # libfranka common utilities
│   └── franka_description/     # URDF/xacro robot description
├── docs/ docs-zh/              # English/Chinese documentation
├── scripts/                    # helper scripts
├── .cursorrules                # Chinese interaction rules (see end of file)
├── .clang-format               # Chromium style (C++11, 100 cols)
├── .clang-tidy                 # C++ linting rules
└── pyproject.toml              # Python ruff config (99 cols, single quotes)
```

## Development Commands

### Clone Dependencies

```bash
vcs import src < src/dependency.repos --recursive --skip-existing
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

### Docker

```bash
docker compose build
docker compose up -d
docker exec -it franka_ros2_humble /bin/bash
# Inside container
vcs import src < src/dependency.repos --recursive --skip-existing
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

| Category | Endpoints |
|----------|-----------|
| Status | GET /api/v1/status/joints, GET /api/v1/status/robot |
| Motion | /api/v1/motion/ptp, /api/v1/motion/move |
| Gripper | /api/v1/gripper/grasp, /api/v1/gripper/homing |
| Special | POST /api/v1/error_recovery, WebSocket /ws |
| Dashboard | static HTML at root / |

ROS subscriptions: /joint_states, /franka_robot_state_broadcaster/robot_state

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

## Important Config Files

| File | Purpose |
|------|---------|
| franka_bringup/config/franka.config.yaml | robot IP, namespace, robot_type (fr3/panda), controller selection |
| franka_bringup/config/controllers.yaml | controller_manager config (update_rate: 1000Hz, thread_priority: 98) |
| franka_bringup/config/tmr.config.yaml | TMR mobile robot config |
| franka_api_server/config/api_server.yaml | API server config |
| src/dependency.repos | external VCS deps (libfranka 0.20.4, franka_description 2.7.0) |
| limits.conf | real-time kernel limits (rtprio 99, memlock unlimited) |

## CI/CD

- **CI** (.github/workflows/ci.yml): Ubuntu latest container, build + test + clang-tidy
- **Release** (.github/workflows/release.yml): git tag triggered, extracts version notes from CHANGELOG.rst
- **Jenkinsfile**: additional CI config

## Documentation

- **English**: README.md, docs/
- **Chinese**: docs-zh/ (quick-start, install-guide-jazzy, moveit_launch_study, etc.)
- **Per-package**: */doc/index.rst or */README.md
- **Official**: https://frankarobotics.github.io/docs

## AI Assistant Guidelines

**Interaction language**: Chinese. **Documentation output**: Chinese, default to docs-zh/ directory.

**Known limitations**:
- franka_ros2 is in rapid development; breaking changes are expected
- franka_mobile_sensors is ignored by COLCON_IGNORE by default; delete that file to enable it
- libfranka UDP requires a real-time kernel; Docker Desktop is not recommended (use Docker Engine)
