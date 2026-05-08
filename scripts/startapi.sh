#!/bin/bash

# ==============================================================================
# Franka ROS 2 API Server 启动脚本
# 描述: 加载环境变量并启动 Franka API Server 服务
# ==============================================================================

echo "正在清理可能残留的 api_server 进程..."
killall -9 api_server 2>/dev/null
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

echo "==============================================================================="
echo "环境加载成功！"
echo "正在启动 Franka API Server 及其前端服务..."
echo "API 及前端面板访问地址: http://localhost:8080"
echo "按 Ctrl+C 停止进程。"
echo "==============================================================================="

# 延迟2秒后自动在浏览器中打开前端面板 (如需禁用可注释此行)
(sleep 2 && python3 -m webbrowser "http://localhost:8080") &

ros2 launch franka_api_server api_server.launch.py
