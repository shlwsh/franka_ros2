#!/bin/bash

# ==============================================================================
# Franka ROS 2 (Jazzy) 快速测试启动脚本
# 描述: 自动清理旧进程、加载环境变量并使用假硬件接口启动 MoveIt 及 RViz，
#       用于在没有真实物理机械臂连接时进行轨迹规划测试验证。
# 注意: fake hardware 模式使用 position command interface（而非 effort），
#       因为 mock_components/GenericSystem 的 effort 接口不会转换为位置变化。
# ==============================================================================

echo "正在清理可能残留的 ROS 2 进程..."
killall -9 ros2_control_node move_group rviz2 joint_state_publisher robot_state_publisher api_server 2>/dev/null
sleep 1

# 获取工作空间路径，脚本在 scripts 下，工作空间根目录是其上一级
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

# 使用 fake hardware 专用的 position 控制器配置替换默认的 effort 配置
# 原因: mock_components/GenericSystem 的 effort 接口不会改变关节位置
MOVEIT_CONFIG_DIR="$(ros2 pkg prefix franka_fr3_moveit_config)/share/franka_fr3_moveit_config/config"
FAKE_CTRL_CONFIG="${WORKSPACE_DIR}/franka_fr3_moveit_config/config/fr3_ros_controllers_fake.yaml"
if [ -f "${FAKE_CTRL_CONFIG}" ]; then
    echo "正在安装 fake hardware 专用控制器配置 (position 模式)..."
    cp "${FAKE_CTRL_CONFIG}" "${MOVEIT_CONFIG_DIR}/fr3_ros_controllers.yaml"
    echo "已将 fr3_ros_controllers.yaml 替换为 position command interface 版本"
fi

echo "==============================================================================="
echo "环境加载成功！"
echo "正在启动 MoveIt 和假硬件 (use_fake_hardware:=true)..."
echo "控制器模式: position (适配 fake hardware)"
echo "启动后，请在 RViz 的 MotionPlanning 面板中进行操作。"
echo "按 Ctrl+C 停止进程。"
echo "==============================================================================="

ros2 launch franka_fr3_moveit_config moveit.launch.py robot_ip:=dont-care use_fake_hardware:=true

