#!/usr/bin/env bash
# 论文 I 闭环 10 trial → run_001.jsonl（阶段 3 / F3-01）
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
LOG_PATH="${LOG_PATH:-${PAPER1_ROOT}/experiments/logs/run_001.jsonl}"
TRIALS="${TRIALS:-10}"
FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000/api/v1}"
FRANKA_API_KEY="${FRANKA_API_KEY:-franka-api-default-key}"

cd "$ROOT"
export PAPER1_ROOT

echo "=== Paper I closed loop ==="
echo "PAPER1_ROOT=$PAPER1_ROOT"
echo "LOG_PATH=$LOG_PATH"

bash scripts/check_paper1_env.sh

# 合成数据（若缺）
if [[ ! -f "${PAPER1_ROOT}/experiments/splits/val.json" ]]; then
  python3 "${PAPER1_ROOT}/scripts/synth_degrade.py"
fi

API_ARGS=()
if curl -sf "${FRANKA_API_BASE}/status/joints?api_key=${FRANKA_API_KEY}" -o /dev/null 2>/dev/null; then
  echo "API 在线：启用 --use-api-motion"
  API_ARGS=(--api-base "$FRANKA_API_BASE" --api-key "$FRANKA_API_KEY" --use-api-motion)
else
  echo "API 未启动：本地 edge_iqa + 路由（无 motion）"
fi

cd "$PAPER1_ROOT"
python3 -m langgraph_router.run \
  --trials "$TRIALS" \
  --log "$LOG_PATH" \
  "${API_ARGS[@]}"

python3 "${ROOT}/scripts/validate_jsonl.py" "$LOG_PATH"
wc -l "$LOG_PATH"
echo "=== Done ==="
