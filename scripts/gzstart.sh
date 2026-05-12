#!/bin/bash

# ==============================================================================
# Franka ROS 2 物理仿真测试启动脚本 (gzstart.sh)
# 描述: 启动 Gazebo 物理仿真环境、加载机器人模型及示例控制器
# ==============================================================================

echo "正在清理可能残留的 Gazebo 和 ROS 2 进程..."
killall -9 ruby gz_sim ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher 2>/dev/null
sleep 1

# 获取工作空间路径
WORKSPACE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "正在加载环境变量..."
if [ -f "/opt/ros/jazzy/setup.bash" ]; then
    source /opt/ros/jazzy/setup.bash
else
    echo "错误: 找不到 ROS 2 Jazzy 环境 (/opt/ros/jazzy/setup.bash)"
    exit 1
fi

if [ -f "${WORKSPACE_DIR}/install/setup.bash" ]; then
    source "${WORKSPACE_DIR}/install/setup.bash"
else
    echo "错误: 找不到工作空间编译产物 (${WORKSPACE_DIR}/install/setup.bash)"
    echo "请先在 ${WORKSPACE_DIR} 目录下执行 colcon build"
    exit 1
fi

# ==============================================================================
# 定义世界模型路径
# 你可以将其替换为你自己的 SDF/World 文件路径
# ==============================================================================
# 默认使用我们创建的 example_table.sdf，包含重力、桌子和障碍物
# 注意：使用绝对路径确保 Gazebo 能找到它
WORLD_FILE="${WORKSPACE_DIR}/franka_gazebo_bringup/worlds/example_table.sdf"

# 如果由于某种原因自定义世界文件不存在，回退到 empty.sdf
if [ ! -f "$WORLD_FILE" ]; then
    echo "警告: 找不到自定义世界文件 $WORLD_FILE，将使用默认空世界。"
    GZ_ARGS="-r empty.sdf"
else
    echo "成功找到自定义世界文件: $WORLD_FILE"
    GZ_ARGS="-r $WORLD_FILE"
fi

echo "==============================================================================="
echo "环境加载成功！"
echo "正在启动 Gazebo 仿真及相关控制器..."
echo "按 Ctrl+C 将停止所有进程。"
echo "==============================================================================="

# 启动 Gazebo 和 Franka 仿真，并在后台运行
# 将控制器指定为 MoveIt 需要的 fr3_arm_controller，同时关闭默认 RViz，以便使用 MoveIt 的 RViz
ros2 launch franka_gazebo_bringup gazebo_franka_arm_example_controller.launch.py \
    robot_type:=fr3 \
    load_gripper:=true \
    controller:=fr3_arm_controller \
    rviz:=false \
    gz_args:="${GZ_ARGS}" &
GAZEBO_PID=$!

sleep 5

echo "正在启动夹爪控制器..."
ros2 run controller_manager spawner fr3_gripper &

echo "正在启动 MoveIt 核心服务..."
ros2 launch franka_fr3_moveit_config gz_moveit.launch.py load_gripper:=true use_fake_hardware:=false &
MOVEIT_PID=$!

sleep 3

echo "正在启动 API Server (前台)..."
echo "API 及前端面板访问地址: http://localhost:8000"
ros2 launch franka_api_server api_server.launch.py

# 脚本退出时清理
echo "收到停止信号，正在清理后台进程..."
kill $GAZEBO_PID $MOVEIT_PID 2>/dev/null
killall -9 ruby gz_sim ros2_control_node move_group rviz2 api_server 2>/dev/null
echo "清理完成！"
