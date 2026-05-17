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
GAZEBO_PID=""
GRIPPER_PID=""
MOVEIT_PID=""
API_PID=""
CLEANED_UP=0

terminate_process() {
    local pid="$1"
    local name="$2"
    local timeout="${3:-8}"
    local signal="${4:-INT}"

    if [ -z "$pid" ] || ! kill -0 "$pid" 2>/dev/null; then
        return
    fi

    echo "正在停止 ${name}..."
    if [ "$signal" = "KILL" ]; then
        kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
        wait "$pid" 2>/dev/null || true
        return
    fi

    kill "-$signal" "-$pid" 2>/dev/null || kill "-$signal" "$pid" 2>/dev/null || true
    for _ in $(seq 1 "$timeout"); do
        if ! kill -0 "$pid" 2>/dev/null; then
            wait "$pid" 2>/dev/null || true
            return
        fi
        sleep 1
    done

    kill -TERM "-$pid" 2>/dev/null || kill -TERM "$pid" 2>/dev/null || true
    sleep 2
    if kill -0 "$pid" 2>/dev/null; then
        kill -KILL "-$pid" 2>/dev/null || kill -KILL "$pid" 2>/dev/null || true
    fi
    wait "$pid" 2>/dev/null || true
}

cleanup() {
    if [ "$CLEANED_UP" -eq 1 ]; then
        return
    fi
    CLEANED_UP=1

    echo "收到停止信号，正在清理后台进程..."
    terminate_process "$API_PID" "API Server" 5
    terminate_process "$MOVEIT_PID" "MoveIt" 1 KILL
    terminate_process "$GRIPPER_PID" "夹爪控制器加载器" 3
    terminate_process "$GAZEBO_PID" "Gazebo" 8
    killall -9 ruby gz_sim ros2_control_node move_group rviz2 api_server 2>/dev/null
    echo "清理完成!"
}

trap cleanup EXIT INT TERM

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

# WSLg/Qt 有时会把 Gazebo/RViz 窗口恢复成不可最大化或不可拖拽的状态。
# 默认强制走 X11/xcb；如需切回 Wayland，可运行：
#   FRANKA_GUI_PLATFORM=wayland ./scripts/gzstart.sh
if [ -n "${WAYLAND_DISPLAY:-}" ] && [ -n "${DISPLAY:-}" ]; then
    export QT_QPA_PLATFORM="${FRANKA_GUI_PLATFORM:-xcb}"
    export GDK_BACKEND=x11
    export QT_AUTO_SCREEN_SCALE_FACTOR=0
    export QT_ENABLE_HIGHDPI_SCALING=0
    echo "检测到 WSLg，已设置 QT_QPA_PLATFORM=${QT_QPA_PLATFORM}。"
fi

# ==============================================================================
# 定义世界模型路径
# 你可以将其替换为你自己的 SDF/World 文件路径
# ==============================================================================
# 默认使用我们创建的 example_table.sdf，包含重力、桌子和障碍物
# 注意：使用绝对路径确保 Gazebo 能找到它
WORLD_FILE="${WORKSPACE_DIR}/franka_gazebo_bringup/worlds/consultation_world.sdf"
GZ_GUI_CONFIG="${WORKSPACE_DIR}/franka_gazebo_bringup/config/franka_gazebo_gui.config"

# 如果由于某种原因自定义世界文件不存在，回退到 empty.sdf
if [ ! -f "$WORLD_FILE" ]; then
    echo "警告: 找不到自定义世界文件 $WORLD_FILE，将使用默认空世界。"
    GZ_ARGS="-r empty.sdf"
else
    echo "成功找到自定义世界文件: $WORLD_FILE"
    GZ_ARGS="-r $WORLD_FILE"
fi

if [ -f "$GZ_GUI_CONFIG" ]; then
    GZ_ARGS="$GZ_ARGS --gui-config $GZ_GUI_CONFIG"
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

# 等待 Gazebo 物理引擎和 ros2_control 完全初始化（包括时钟同步）
echo "等待 Gazebo 物理引擎完全初始化（约15秒）..."
sleep 15

# 检查 Gazebo 是否还在运行
if ! kill -0 "$GAZEBO_PID" 2>/dev/null; then
    echo "错误: Gazebo 进程已退出，请检查日志。"
    exit 1
fi

# 等待 controller_manager 服务可用后再加载夹爪控制器
echo "正在启动夹爪控制器..."
ros2 run controller_manager spawner fr3_gripper \
    --controller-manager-timeout 30 2>&1 | grep -v "already loaded" &
GRIPPER_PID=$!

# 等待夹爪控制器加载完成
sleep 3

echo "正在启动 MoveIt 核心服务..."
ros2 launch franka_fr3_moveit_config gz_moveit.launch.py load_gripper:=true use_fake_hardware:=false &
MOVEIT_PID=$!

# 等待 MoveIt 和 TF 树完全就绪
sleep 8

echo "正在启动 API Server..."
echo "API 及前端面板访问地址: http://localhost:8000"
ros2 launch franka_api_server api_server.launch.py &
API_PID=$!

echo "==============================================================================="
echo "所有服务已启动完毕！按 Ctrl+C 停止所有进程。"
echo "==============================================================================="

# 等待所有核心后台进程；任何一个退出则脚本结束并触发 cleanup
wait -n "$GAZEBO_PID" "$MOVEIT_PID" "$API_PID" 2>/dev/null || true
echo "检测到某个核心进程已退出。"

