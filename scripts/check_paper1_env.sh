#!/usr/bin/env bash
# 论文 I 环境检查（doctor/paper1 与本仓一体）
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
export PAPER1_ROOT
FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000}"

echo "🔍 论文 I 环境检查 (franka_ros2)"
echo "   工作区: $ROOT"
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
check "doctor/paper1 目录" "test -d \"$PAPER1_ROOT\""
check "paper1 README" "test -f \"$PAPER1_ROOT/README.md\""
check "edge_iqa 目录" "test -d \"$PAPER1_ROOT/edge_iqa\""
check "langgraph_router 目录" "test -d \"$PAPER1_ROOT/langgraph_router\""
check "franka_bridge 客户端" "test -f \"$PAPER1_ROOT/sim/franka_bridge/client.py\""
check "poses.yaml" "test -f franka_api_server/franka_api_server/skills/poses.yaml"
check "vision 路由" "test -f franka_api_server/franka_api_server/routers/vision.py"
check "skills_loader" "test -f franka_api_server/franka_api_server/services/skills_loader.py"
check "Fig.1 素材" \
  "test -f \"$PAPER1_ROOT/figures/fig1_system_overview.svg\" || test -f \"$PAPER1_ROOT/figures/fig1_system_overview.pdf\""
check "edge_iqa scorer" "test -f \"$PAPER1_ROOT/edge_iqa/scorer.py\""
check "latency_benchmark.json" "test -f \"$PAPER1_ROOT/experiments/edge_iqa/latency_benchmark.json\""
check "recommended_tau.json" "test -f \"$PAPER1_ROOT/experiments/results/recommended_tau.json\""
check "langgraph_router/run.py" "test -f \"$PAPER1_ROOT/langgraph_router/run.py\""
check "run_001.jsonl" "test -f \"$PAPER1_ROOT/experiments/logs/run_001.jsonl\""
check "main_exp.yaml" "test -f \"$PAPER1_ROOT/experiments/configs/main_exp.yaml\""
check "main_seed0.csv" "test -f \"$PAPER1_ROOT/experiments/results/main_seed0.csv\""
check "fig5_rtt_cdf.pdf" "test -f \"$PAPER1_ROOT/figures/fig5_rtt_cdf.pdf\""
check "franka_m6_rtt.csv" "test -f \"$PAPER1_ROOT/experiments/results/franka_m6_rtt.csv\""
check "latex main.pdf" "test -f \"$PAPER1_ROOT/latex/main.pdf\""
check "fig7 ablation" "test -f \"$PAPER1_ROOT/figures/fig7_ablation_tau.pdf\""
check "submission package" "test -f \"$PAPER1_ROOT/submission/RA-L_20260529/manuscript.pdf\""
check "latex main-zh.pdf" "test -f \"$PAPER1_ROOT/latex/main-zh.pdf\""

if curl -sf "${FRANKA_API_BASE%/api/v1}/" -o /dev/null 2>/dev/null || \
   curl -sf "${FRANKA_API_BASE}/status/joints?api_key=${FRANKA_API_KEY:-franka-api-default-key}" -o /dev/null 2>/dev/null; then
  echo "✅ API 可访问 ($FRANKA_API_BASE)"
  ok=$((ok + 1))

  if curl -sf "${FRANKA_API_BASE}/motion/skills?api_key=${FRANKA_API_KEY:-franka-api-default-key}" -o /dev/null; then
    echo "✅ skills API"
    ok=$((ok + 1))
  else
    echo "❌ skills API"
    fail=$((fail + 1))
  fi
else
  echo "⚠️  API 未启动（先运行 scripts/testall.sh）"
fi

echo ""
echo "通过: $ok  失败: $fail"
echo "详见 docs-zh/paper1/V19/phases/阶段1_系统基座与架构证据.md"

if [[ "$fail" -gt 0 ]]; then
  exit 1
fi
exit 0
