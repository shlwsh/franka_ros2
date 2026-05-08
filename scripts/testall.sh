#!/bin/bash

# ==============================================================================
# Franka ROS 2 统一测试启动脚本 (testall.sh)
# 描述: 一键启动 MoveIt 假硬件环境、RViz 以及 API 前端服务
# ==============================================================================

echo "正在清理可能残留的 ROS 2 进程..."
killall -9 ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher api_server 2>/dev/null
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

# 使用 fake hardware 专用的 position 控制器配置
MOVEIT_CONFIG_DIR="$(ros2 pkg prefix franka_fr3_moveit_config)/share/franka_fr3_moveit_config/config"
FAKE_CTRL_CONFIG="${WORKSPACE_DIR}/franka_fr3_moveit_config/config/fr3_ros_controllers_fake.yaml"
if [ -f "${FAKE_CTRL_CONFIG}" ]; then
    echo "正在安装 fake hardware 专用控制器配置 (position 模式)..."
    cp "${FAKE_CTRL_CONFIG}" "${MOVEIT_CONFIG_DIR}/fr3_ros_controllers.yaml"
fi

echo "==============================================================================="
echo "环境加载成功！"
echo "正在启动 MoveIt 与 RViz (后台运行)..."
ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true &
MOVEIT_PID=$!

# 给 MoveIt 一些启动时间
sleep 3

echo "正在启动 Franka API Server 及其前端服务 (前台运行)..."
echo "API 及前端面板访问地址: http://localhost:8080"
echo "按 Ctrl+C 将停止所有进程。"
echo "==============================================================================="

# 延迟2秒后自动打开浏览器
(sleep 2 && python3 -m webbrowser "http://localhost:8080") &

# 前台运行 API Server，接收 Ctrl+C 信号
ros2 launch franka_api_server api_server.launch.py

# 脚本退出时（如按下 Ctrl+C），自动清理后台的 MoveIt 进程
echo "收到停止信号，正在清理后台进程..."
kill $MOVEIT_PID 2>/dev/null
killall -9 ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher api_server 2>/dev/null
echo "清理完成！"
