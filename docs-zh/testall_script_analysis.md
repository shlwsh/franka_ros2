# testall.sh 脚本分析

> 文档版本：2026-05-12
> 对应脚本：`scripts/testall.sh`

## 概述

`testall.sh` 是一个一键启动 Franka ROS 2 环境的统一脚本，用于启动 MoveIt + RViz 假硬件环境以及 API Server 前端服务。它不连接真实机器人，适合在没有物理机械臂的情况下进行开发、调试和演示。

---

## 脚本执行流程

```
testall.sh
  │
  ├─ 1. 清理残留进程
  │     killall -9 ros2_control_node move_group rviz2 ...
  │
  ├─ 2. 加载 ROS 2 Jazzy 环境
  │     source /opt/ros/jazzy/setup.bash
  │     source <workspace>/install/setup.bash
  │
  ├─ 3. 覆盖 ros2_control 控制器配置（fake hardware 专用）
  │     cp fr3_ros_controllers_fake.yaml
  │        → <install>/franka_fr3_moveit_config/config/fr3_ros_controllers.yaml
  │
  ├─ 4. 后台启动 MoveIt + RViz
  │     ros2 launch franka_fr3_moveit_config moveit.launch.py \
  │         robot_ip:=dont-care use_fake_hardware:=true
  │
  └─ 5. 前台启动 API Server（Ctrl+C 终止时清理后台进程）
        ros2 launch franka_api_server api_server.launch.py
```

---

## 当前使用的机械臂

脚本启动的是 **FR3（Franka Research 3）** 7自由度机械臂，通过 `use_fake_hardware:=true` 使用 **模拟硬件（Mock Hardware）**，不连接真实机器人。

---

## 世界模型配置文件

MoveIt 的世界模型由以下配置文件构成，全部位于 `franka_fr3_moveit_config/config/` 目录下：

### 1. kinematics.yaml — 运动学模型

定义逆运动学求解器插件及其参数：

```yaml
fr3_arm:
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin
  kinematics_solver_search_resolution: 0.005  # 搜索分辨率 (rad)
  kinematics_solver_timeout: 0.005             # 单次求解超时 (s)
```

- 使用 **KDL 插件**（Orocos Kinematics and Dynamics Library）
- `fr3_arm` 与 `fr3_controllers.yaml` 中定义的规划组名称对应
- 搜索分辨率和超时可根据规划速度需求调整

### 2. joint_limits.yaml — 关节限位

定义 7 个关节的速度和加速度软限制：

| 关节 | 最大速度 (rad/s) | 最大加速度 (rad/s²) |
|------|-----------------|-------------------|
| fr3_joint1 | 2.62 | 3.75 |
| fr3_joint2 | 2.62 | 1.875 |
| fr3_joint3 | 2.62 | 2.5 |
| fr3_joint4 | 2.62 | 3.125 |
| fr3_joint5 | 5.26 | 3.75 |
| fr3_joint6 | 4.18 | 5.0 |
| fr3_joint7 | 5.26 | 5.0 |

> 注意：此处的限位是 MoveIt 规划层的软限制，与机器人本身的硬件限位独立。

### 3. fr3.srdf.xacro — 语义模型（SRDF）

通过 xacro 宏生成，源文件位于：

```
franka_description/robots/common/franka_arm.srdf.xacro
```

由 `fr3.srdf.xacro` → `franka_arm.srdf.xacro` 中的 `franka_arm_srdf` 宏展开，包含：

- **虚拟关节**（virtual joints）— 连接机器人与世界坐标系
- **规划组**（planning groups）— 定义哪些关节/连杆属于同一规划集合
- **末端执行器**（end effectors）— 定义 TCP（工具中心点）
- **自碰撞矩阵**（disabled collision pairs）— 忽略不会发生碰撞的连杆对
- **默认机器人姿态**（default robot poses）— 如"ready"、"extended"等预定义姿态

### 4. ompl_planning.yaml — 规划算法配置

定义 OMPL（Open Motion Planning Library）中各算法的具体参数，包括：

- 各算法的规划超时时间（`planner_timeout`）
- 迭代参数（`max_iterations`）
- 范围参数（`range`）
- 等效于 MoveIt 的 `ompl_planning.yaml` 配置文件

### 5. fr3_controllers.yaml — 控制器映射

将 MoveIt 的逻辑控制器名称映射到实际 ros2_control 控制器：

```yaml
controller_names:
  - fr3_arm_controller
  - fr3_gripper

fr3_arm_controller:
  action_ns: follow_joint_trajectory
  type: FollowJointTrajectory   # MoveIt 期望的轨迹执行接口
  default: true
  joints:
    - fr3_joint1
    - fr3_joint2
    - fr3_joint3
    - fr3_joint4
    - fr3_joint5
    - fr3_joint6
    - fr3_joint7

fr3_gripper:
    action_ns: gripper_action
    type: GripperCommand
    default: true
    joints:
      - fr3_finger_joint1
      - fr3_finger_joint2
```

### 6. fr3_ros_controllers_fake.yaml — ros2_control fake 硬件配置

由脚本动态覆盖到安装目录，用于 fake hardware 模式。关键区别是将 `command_interfaces` 从 `effort`（真实机器人）改为 `position`（模拟）：

```yaml
/**:  # 全局命名空间
  controller_manager:
    ros__parameters:
      update_rate: 100  # Hz

  fr3_arm_controller:
    ros__parameters:
      command_interfaces:
        - position        # 真实机器人用 effort，fake 用 position
      state_interfaces:
        - position
        - velocity
      joints:
        - fr3_joint1
        - fr3_joint2
        - fr3_joint3
        - fr3_joint4
        - fr3_joint5
        - fr3_joint6
        - fr3_joint7
```

> **原因**：`mock_components/GenericSystem` 的 effort 接口不会自动转换为位置变化，必须使用 position 接口才能在仿真中看到关节运动。

---

## 世界模型加载链路

```
moveit.launch.py
  │
  ├─ xacro ──> fr3.urdf.xacro ──> franka_arm.urdf.xacro
  │           （物理模型：连杆、关节、碰撞体、惯性参数）
  │           参数: hand, robot_ip, use_fake_hardware, ros2_control 等
  │
  ├─ xacro ──> fr3.srdf.xacro ──> franka_arm.srdf.xacro
  │           （语义模型：规划组、碰撞矩阵、末端执行器、默认姿态）
  │           参数: hand, ee_id
  │
  ├─ kinematics.yaml        ──> KDL 运动学求解器参数
  ├─ joint_limits.yaml      ──> 各关节速度/加速度限位
  ├─ ompl_planning.yaml     ──> OMPL 规划算法参数
  └─ fr3_controllers.yaml   ──> MoveIt → ros2_control 控制器映射
```

---

## 配置调整指南

### 调整 1：切换到 Panda 机械臂

需要切换整个 MoveIt 配置包：

```bash
# 修改 testall.sh 中的 launch 包名
ros2 launch franka_panda_moveit_config moveit.launch.py \
    robot_ip:=dont-care use_fake_hardware:=true
```

同时修改 `FAKE_CTRL_CONFIG` 路径指向 Panda 的 fake 控制器配置文件。

### 调整 2：修改运动学求解器

编辑 `kinematics.yaml`，替换求解器插件：

```yaml
fr3_arm:
  # 默认 KDL（适合大多数场景）
  kinematics_solver: kdl_kinematics_plugin/KDLKinematicsPlugin

  # 可选：IKFast（需预先生成 IKFast 插件，适合高速重复求解）
  # kinematics_solver: ikfast_kinematics_plugin/IKFastKinematicsPlugin

  # 可选：TRAC-IK（比 KDL 更鲁棒，适合奇异位形附近）
  # kinematics_solver: trac_ik_kinematics_plugin/TRACIKKinematicsPlugin

  kinematics_solver_search_resolution: 0.005
  kinematics_solver_timeout: 0.005
```

### 调整 3：修改关节限位

直接编辑 `joint_limits.yaml`，例如放宽关节 5 的速度限制：

```yaml
fr3_joint5:
  has_velocity_limits: true
  max_velocity: 6.0          # 从 5.26 改为 6.0
  has_acceleration_limits: true
  max_acceleration: 4.0       # 从 3.75 改为 4.0
```

### 调整 4：修改 SRDF（规划组、碰撞矩阵、默认姿态）

SRDF 通过 xacro 宏生成，需修改源文件后重新编译：

```
源文件：franka_description/robots/common/franka_arm.srdf.xacro
```

常见调整场景：

- 添加/修改规划组（例如将多个机械臂合并为一个规划组）
- 调整自碰撞矩阵（减少或增加允许碰撞的连杆对）
- 修改默认姿态（例如改变"ready"位置的关节角度）
- 更改末端执行器定义

修改后重新编译：

```bash
colcon build --packages-select franka_description
```

### 调整 5：修改 OMPL 规划算法参数

编辑 `ompl_planning.yaml`，例如调整 RRT-Connect 的规划时间：

```yaml
RRTConnectkConfigDefault:
  range: 0.0              # 0 表示不限制采样范围
  planner_timeout: 0.5    # 从默认值改为 0.5s
```

> 常用算法对比：
> - **RRTConnect**：快速探索，适合高维空间
> - **PRM**：概率路线图，适合多次查询
> - **SBL**：基于抽取的碰撞查询，适合约束规划
> - **EST**：扩展随机树，适合窄通道

### 调整 6：修改 ros2_control 控制器接口

编辑 `fr3_ros_controllers_fake.yaml`，更改控制器接口类型：

```yaml
fr3_arm_controller:
  ros__parameters:
    command_interfaces:
      - position    # 当前 fake 模式：位置控制
      # - velocity  # 可选：速度控制
      # - effort    # 真实机器人用：力矩控制（需要真实硬件）
    state_interfaces:
      - position
      - velocity
```

### 调整 7：修改 URDF/xacro 物理参数（如 TCP 偏移）

URDF xacro 参数在 `moveit.launch.py` 中通过 xacro 命令行传递：

```python
robot_description_config = Command(
    [FindExecutable(name='xacro'), ' ', fr3_xacro_file,
     ' hand:=', load_gripper,           # 是否加载夹爪 (true/false)
     ' robot_ip:=', robot_ip,
     ' ee_id:=', ee_id,                 # 末端执行器 ID
     ' use_fake_hardware:=', use_fake_hardware,
     ' ros2_control:=true'])
```

常见的 xacro 参数（定义在 `fr3.urdf.xacro` 中）：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `hand` | `true` | 是否加载 Franka Hand 夹爪 |
| `ee_id` | `franka_hand` | 末端执行器 ID：`franka_hand`、`cobot_pump`、`none` |
| `tcp_xyz` | `0 0 0.1034` | TCP 相对于末端执行器框架的位置偏移 |
| `tcp_rpy` | `0 0 0` | TCP 相对于末端执行器框架的姿态偏移 |
| `safety_distance` | `0.03` | 碰撞胶囊的安全距离 |
| `xyz` | `0 0 0` | 机器人相对于世界坐标系的位置偏移 |
| `rpy` | `0 0 0` | 机器人相对于世界坐标系的姿态偏移 |

如需持久化修改 TCP 偏移，直接编辑 `fr3.urdf.xacro` 中的对应参数定义行：

```xacro
<!-- fr3.urdf.xacro -->
<xacro:arg name="tcp_xyz" default="0 0 0.1034"/>
<xacro:arg name="tcp_rpy" default="0 0 0"/>
```

---

## 配置速查表

| 你想修改的内容 | 对应配置文件 |
|---|---|
| 运动学求解器类型及参数 | `kinematics.yaml` |
| 关节速度/加速度限制 | `joint_limits.yaml` |
| 规划组、碰撞矩阵、默认姿态 | `franka_arm.srdf.xacro` → 重新编译 |
| 规划算法选择及参数 | `ompl_planning.yaml` |
| MoveIt → ros2_control 映射 | `fr3_controllers.yaml` |
| ros2_control 控制器接口类型 | `fr3_ros_controllers_fake.yaml` |
| 连杆几何、物理参数、碰撞体 | `fr3.urdf.xacro` / `franka_arm.urdf.xacro` |
| 是否加载夹爪、TCP 偏移 | `moveit.launch.py` 中的 xacro 参数传递 |
