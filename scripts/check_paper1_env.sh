#!/usr/bin/env bash
# 论文 I 双仓环境检查（F0-03）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PAPER1_ROOT="${PAPER1_ROOT:-/mnt/e/work/ppt-builder/doctor/paper1}"
FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000}"

echo "🔍 论文 I 环境检查 (franka_ros2)"
echo "   PAPER1_ROOT=$PAPER1_ROOT"
echo ""

ok=0
fail=0

check() {
  if eval "$2" &>/dev/null; then
    echo "✅ $1"
    ok=$((ok + 1))
  else
    echo "❌ $1"
    fail=$((fail + 1))
  fi
}

check "Git 仓库" "git rev-parse --git-dir"
check "colcon install" "test -f install/setup.bash"
check "ROS Jazzy" "test -f /opt/ros/jazzy/setup.bash"
check "PAPER1_ROOT 存在" "test -d \"$PAPER1_ROOT\""
check "edge_iqa 目录（或占位 README）" \
  "test -d \"$PAPER1_ROOT/edge_iqa\" || test -f \"$PAPER1_ROOT/README.md\""
check "franka_api_server 包" "test -d franka_api_server/franka_api_server"
check "vision 路由（待实现）" \
  "test -f franka_api_server/franka_api_server/routers/vision.py" || true

if curl -sf "${FRANKA_API_BASE%/api/v1}/" -o /dev/null 2>/dev/null || \
   curl -sf "${FRANKA_API_BASE}/status/joints?api_key=${FRANKA_API_KEY:-franka-api-default-key}" -o /dev/null 2>/dev/null; then
  echo "✅ API 可访问 ($FRANKA_API_BASE)"
  ok=$((ok + 1))
else
  echo "⚠️  API 未启动（先运行 scripts/testall.sh）"
fi

echo ""
echo "通过: $ok  待办/失败: $fail"
echo "详见 docs-zh/paper1/V19/franka_ros2_优化改进计划.md"

exit 0
