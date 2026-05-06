# Franka ROS 2 项目说明文档

## 项目概述
**franka_ros2** 是基于 ROS 2 框架为 Franka Robotics 科研机器人（如 FR3 等）开发的官方集成包。本项目深度封装了 `libfranka`，将 Franka 机器人的控制接口无缝接入 ROS 2 生态系统。它主要用于机器人相关的科学研究与开发，为开发者提供了稳定、强大且高效的机器人控制与状态读取能力。

## 技术架构
本项目采用了现代化的 ROS 2 开发架构，其核心技术栈及组件交互如下：
- **ROS 2 基础层**：基于 **ROS 2 Humble** 进行开发，采用 DDS 作为通信中间件，提供节点间的通信功能。
- **底层驱动层 (`libfranka`)**：通过与 Franka 机械臂硬件的 UDP 实时通信，实现高频率（1kHz）的控制指令下发与状态反馈。
- **硬件接口层 (`ros2_control`)**：通过自定义的 `franka_hardware` 插件接入 ROS 2 的 `ros2_control` 框架，使上层控制器可以使用标准的 ROS 2 接口来控制 Franka 机械臂。
- **运动规划层 (MoveIt 2)**：集成 MoveIt 2，支持碰撞检测、轨迹规划、逆运动学求解等高级机械臂操作。
- **仿真环境层 (Gazebo)**：提供与 Gazebo 仿真器的集成配置，支持开发者在无实体机器人的情况下进行算法验证。

## 目录结构及各包的作用

当前项目是一个包含多个子包（Packages）的 ROS 2 工作空间，各主要目录的作用如下：

| 目录 / 包名 | 作用说明 |
| :--- | :--- |
| **`franka_ros2`** | 项目元包（Meta package），方便整体构建和依赖管理。 |
| **`franka_bringup`** | 核心启动包。包含用于启动和配置机器人的 `launch` 文件以及运行时所需的基础参数配置文件。 |
| **`franka_hardware`** | 提供连接实体机器人和 `ros2_control` 架构的硬件抽象接口（Hardware Interfaces）。 |
| **`franka_example_controllers`** | 提供多种 `ros2_control` 的控制器示例代码（如关节阻抗控制、笛卡尔速度控制等），方便开发者参考和二次开发。 |
| **`franka_fr3_moveit_config`** | Franka 机器人的 MoveIt 2 配置文件包，包含 URDF、SRDF 以及运动规划的各项配置参数。 |
| **`franka_gripper`** | Franka 夹爪（Franka Hand）的 ROS 2 控制节点与接口实现。 |
| **`franka_msgs`** | 定义了专门用于 Franka 机器人的自定义 ROS 2 消息 (Messages) 和动作 (Actions)。 |
| **`franka_robot_state_broadcaster`** | 状态广播器。用于将机械臂的内部特定状态通过 ROS 2 话题实时发布出来。 |
| **`franka_semantic_components`** | 为 `ros2_control` 提供 Franka 机器人专用的语义组件（Semantic Components）。 |
| **`franka_gazebo_bringup`** | 包含用于在 Gazebo 仿真器中启动 Franka 机器人的 `launch` 文件。 |
| **`franka_mobile`** / **`franka_mobile_sensors`** | 针对 Franka 移动协作机器人（TMR）及相关传感器提供的支持包。 |
| **`docs/`** | 官方原始存放部分相关说明文档的目录。 |

## 最终效果
部署本项目后，开发者将获得以下能力：
1. **实时控制**：在 ROS 2 环境中，以高频率对 Franka 机械臂和夹爪执行精准的运动控制。
2. **状态监测**：实时读取末端执行器位姿、各关节角度、力矩等底层数据。
3. **快速开发**：能够直接复用 MoveIt 2 库进行路径规划，或者编写自定义的 `ros2_control` 控制器来实现复杂的力控/阻抗控制算法。
4. **数字孪生/仿真**：在 Gazebo 中测试自己的算法逻辑，并在不更改核心逻辑的情况下平滑迁移到真实硬件上。

## 如何启动和使用

### 1. 环境准备
项目基于 **ROS 2 Humble** 构建。推荐使用 Ubuntu 22.04。除了本地编译外，项目也推荐使用 Docker 环境（或 VSCode Dev Containers）以避免污染本地宿主机环境。

### 2. 编译项目 (本地方式)
确保已安装 ROS 2 Humble 及相关依赖（如 `ros-dev-tools`）。
```bash
# 1. 创建工作空间并拉取代码
mkdir -p ~/franka_ros2_ws/src
cd ~/franka_ros2_ws
git clone https://github.com/frankarobotics/franka_ros2.git src

# 2. 拉取所有依赖
vcs import src < src/dependency.repos --recursive --skip-existing

# 3. 安装 rosdep 依赖
rosdep install --from-paths src --ignore-src --rosdistro humble -y

# 4. 编译并加载环境变量
colcon build --symlink-install --cmake-args -DCMAKE_BUILD_TYPE=Release -DBUILD_TESTS=OFF
source install/setup.sh
```

### 3. 运行测试与示例

- **运行虚拟硬件 (MoveIt 2 演示)**
  如果你目前没有连接真实机械臂，可以运行带有虚拟硬件的 MoveIt 演示：
  ```bash
  ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true
  ```

- **运行真实机器人的控制器示例**
  配置好真实的 `franka.config.yaml`（填写正确的机械臂 IP），然后运行示例控制器（如 `joint_impedance_example_controller`）：
  ```bash
  ros2 launch franka_bringup example.launch.py controller_name:=joint_impedance_example_controller
  ```

- **移动协作机器人 (TMR) 控制**
  可以通过手柄进行遥控：
  ```bash
  ros2 launch franka_bringup mobile_teleop.launch.py
  ```

### 4. 注意事项
由于项目与机械臂之间采用 UDP 高频通信，请务必保证：
1. **网络连接**：直接使用网线连接计算机与机器人控制器。
2. **实时系统**：为了避免 "UDP receive: Timeout error"，宿主机系统必须配置**实时内核 (Real-time kernel)**。如果使用 Docker，必须使用 Docker Engine，而不能使用不具备足够实时性能的 Docker Desktop。

---

> 本文档由 AI 助手在 `docs-zh` 目录下生成。如有疑问或需要调整补充，请随时提出。
