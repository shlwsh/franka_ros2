# Franka ROS 2 仿真启动脚本 (gzstart.sh) 分析报告

## 1. 脚本概述

`scripts/gzstart.sh` 是 Franka ROS 2 项目中用于一键启动基于 Gazebo 物理引擎的完整仿真环境的脚本。它不仅启动了包含重力和碰撞模型的物理仿真，还串联启动了 MoveIt 运动规划服务、机器人的各个关节控制器以及顶层的 API 服务。

该脚本主要用于在纯软件环境（无真实机械臂硬件）下，高保真地模拟机器人的物理行为和运动学/动力学特性。

## 2. 详细执行流程解析

脚本的执行逻辑按顺序可以划分为以下几个关键阶段：

### 2.1 清理历史环境
```bash
killall -9 ruby gz_sim ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher 2>/dev/null
```
在启动任何新服务前，脚本会强制终止系统中可能残留的 Gazebo 进程（`ruby`, `gz_sim`）、ROS 2 控制节点、MoveIt 进程（`move_group`）、RViz 以及状态发布器。这一步对于避免端口占用和 ROS 节点名称冲突至关重要，特别是物理仿真进程常常在异常中断时不会自行清理。

### 2.2 加载环境变量
```bash
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
source /opt/ros/jazzy/setup.bash
source "${WORKSPACE_DIR}/install/setup.bash"
```
脚本首先获取当前工作空间的绝对路径，接着严格按顺序加载底层的 ROS 2 发行版环境（**Jazzy**）以及当前项目编译输出的 `install/setup.bash`。如果缺失上述任何一个环境配置，脚本将直接报错并终止运行。

### 2.3 准备 Gazebo 仿真世界
```bash
WORLD_FILE="${WORKSPACE_DIR}/franka_gazebo_bringup/worlds/example_table.sdf"
```
脚本指定了一个自定义的仿真场景文件 `example_table.sdf`，该场景预先配置了重力环境、工作台结构以及可能的障碍物。如果脚本检测到该文件不存在，则具有良好的容错机制，会自动回退使用 Gazebo 默认的空场景 (`empty.sdf`)。

### 2.4 启动核心仿真节点与控制器
```bash
ros2 launch franka_gazebo_bringup gazebo_franka_arm_example_controller.launch.py \
    robot_type:=fr3 \
    load_gripper:=true \
    controller:=fr3_arm_controller \
    rviz:=false \
    gz_args:="${GZ_ARGS}" &
```
这是脚本的核心步骤之一，在后台启动 Gazebo 及 Franka 的硬件抽象层仿真。值得注意的关键参数包括：
- `controller:=fr3_arm_controller`：指定加载标准的机械臂关节轨迹控制器 (Joint Trajectory Controller)，这是后续 MoveIt 下发真实运动轨迹时必需的执行接口。
- `rviz:=false`：主动关闭此 Launch 文件自带的 RViz 实例，以防止与后续 MoveIt 启动的带有运动规划面板的 RViz 实例发生冲突。

### 2.5 启动夹爪控制器
```bash
ros2 run controller_manager spawner fr3_gripper &
```
单独调用 `controller_manager` 启动针对 Franka 末端执行器（夹爪）的控制器 (`fr3_gripper`)。这确保了在仿真环境中，机械臂不仅能移动，其夹爪也能正常响应开合控制指令。

### 2.6 启动 MoveIt 运动规划服务
```bash
ros2 launch franka_fr3_moveit_config gz_moveit.launch.py load_gripper:=true use_fake_hardware:=false &
```
启动 MoveIt 核心服务流，这里的关键在于参数 `use_fake_hardware:=false`。由于前面已经启动了 Gazebo 物理仿真来提供底层的物理反馈和接口响应，所以明确告知 MoveIt 不使用它自带的"伪硬件(Fake Hardware)"插件。

### 2.7 启动顶层 API 服务
```bash
ros2 launch franka_api_server api_server.launch.py
```
最后，脚本在前台启动项目中自定义的 `franka_api_server` 节点，对外暴露 RESTful 和 WebSocket 接口（默认监听在 8000 端口）。此时，用户（或前端 Web 面板）可以通过这些接口发送高阶指令，API Server 接收到指令后转化为 ROS Action 发送给 MoveIt 进行运动规划，最终下发至 Gazebo 物理引擎执行。

### 2.8 优雅退出与进程回收
```bash
kill $GAZEBO_PID $MOVEIT_PID 2>/dev/null
killall -9 ruby gz_sim ros2_control_node move_group rviz2 api_server 2>/dev/null
```
利用 Bash 脚本的按序执行机制，当用户在前台通过 `Ctrl+C` 终止 API 服务后，脚本会继续执行末尾的清理指令，杀掉之前放入后台的 Gazebo (`GAZEBO_PID`) 和 MoveIt (`MOVEIT_PID`) 进程组，确保系统资源被完整释放，不遗留“僵尸”进程。

## 3. 总结与注意事项

- **运行前提**：当前配置强依赖于 ROS 2 Jazzy 发行版，且在运行前必须已经在工作区执行过 `colcon build` 编译产出相应包。
- **与 `scripts/start.sh` 的区别**：
  - 本脚本 (`gzstart.sh`)：引入了完整的 Gazebo 物理引擎，进行包含重力、碰撞、动力学的**高保真物理仿真**。对计算资源消耗较大，但测试结果更贴近真实物理世界。
  - `start.sh` 脚本：使用的是 MoveIt 内部的 Fake Hardware 接口，它仅仅进行运动学的数学推导（在 RViz 中看动画），没有物理引擎计算。启动快、资源消耗小，主要用于测试 API 逻辑和路径规划算法是否连通。
- **排错建议**：如果启动失败或卡顿，首先应检查 `ruby` 或 `gz_sim` 进程是否因之前非正常终止而挂死；其次，检查终端输出是否提示 `fr3_arm_controller` 加载失败，如果控制器未能启动，MoveIt 将无法发送控制轨迹。
