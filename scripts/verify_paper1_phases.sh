#!/usr/bin/env bash
# 论文 I 阶段 1+2 自动验证，输出到 docs-zh/paper1/V19/verification/logs/
set -eo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
VER_DIR="${ROOT}/docs-zh/paper1/V19/verification/logs"
mkdir -p "$VER_DIR"
STAMP="$(date -u +%Y%m%dT%H%M%SZ)"
LOG="${VER_DIR}/run_${STAMP}.log"
exec > >(tee -a "$LOG") 2>&1

echo "========== Paper I Phase 1+2 Verification ${STAMP} =========="
export PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
export FRANKA_API_KEY="${FRANKA_API_KEY:-franka-api-default-key}"

echo "--- check_paper1_env.sh ---"
bash scripts/check_paper1_env.sh || true

echo "--- colcon build franka_api_server ---"
if [[ -f /opt/ros/jazzy/setup.bash ]]; then
  set +u
  source /opt/ros/jazzy/setup.bash
  set -u
fi
colcon build --packages-select franka_api_server --symlink-install 2>&1 | tail -5
set +u
source install/setup.bash
set -u

echo "--- paper1 offline ---"
cd "$PAPER1_ROOT"
python3 scripts/synth_degrade.py 2>&1 | tail -3
python3 -m pytest edge_iqa/tests -v 2>&1 | tail -10
python3 -m edge_iqa.cli --image experiments/debug/sample_clear.png --json | tee "${VER_DIR}/cli_sample_${STAMP}.json"
python3 experiments/edge_iqa/calibrate_tau.py 2>&1 | tail -5
python3 experiments/edge_iqa/latency_benchmark.py | tee "${VER_DIR}/latency_${STAMP}.json"
cd "$ROOT"

echo "--- API smoke (uvicorn) ---"
PORT="$(python3 -c 'import socket;s=socket.socket();s.bind(("",0));print(s.getsockname()[1]);s.close()')"
export PAPER1_MODE=1
export FRANKA_API_HOST=127.0.0.1
export FRANKA_API_PORT="${PORT}"

if [[ -d franka_api_server/.venv ]]; then
  PY=franka_api_server/.venv/bin/python
else
  PY=python3
fi

$PY -m uvicorn franka_api_server.app:app --host 127.0.0.1 --port "${PORT}" &
UV_PID=$!
sleep 3
BASE="http://127.0.0.1:${PORT}/api/v1"
KEY="${FRANKA_API_KEY}"

curl -sf "${BASE}/motion/skills?api_key=${KEY}" | tee "${VER_DIR}/skills_list_${STAMP}.json"
echo ""

curl -s -X POST "${BASE}/motion/skills/go_to_tongue_pose?api_key=${KEY}" \
  | tee "${VER_DIR}/skill_tongue_${STAMP}.json" || true
echo ""

CTRL_CODE="$(curl -s -o /dev/null -w '%{http_code}' "${BASE}/controller/list?api_key=${KEY}")"
echo "controller/list HTTP ${CTRL_CODE} (expect 404 under PAPER1_MODE)"
echo "${CTRL_CODE}" > "${VER_DIR}/controller_http_${STAMP}.txt"

IMG="${PAPER1_ROOT}/experiments/synthetic/clear/clear_0000.png"
curl -sf -X POST "${BASE}/vision/evaluate?api_key=${KEY}" \
  -F "file=@${IMG}" | tee "${VER_DIR}/vision_eval_${STAMP}.json"
echo ""

kill "${UV_PID}" 2>/dev/null || true
wait "${UV_PID}" 2>/dev/null || true

echo "--- franka_api_server pytest ---"
unset PAPER1_MODE
cd "${ROOT}/franka_api_server"
if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -q httpx pyyaml python-multipart pytest uvicorn fastapi pydantic numpy Pillow
fi
set +u
source "${ROOT}/install/setup.bash"
set -u
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest test/test_api.py test/test_vision.py test/test_paper1_mode.py -v 2>&1 | tail -25
cd "$ROOT"

echo "--- phase 3 closed loop ---"
bash scripts/paper1_closed_loop.sh 2>&1 | tail -15

echo "--- phase 4 main + M6 ---"
bash scripts/paper1_run_main.sh 2>&1 | tail -8
bash scripts/paper1_run_m6.sh 2>&1 | tail -8
python3 -c "
import csv
from pathlib import Path
r=Path('${PAPER1_ROOT}/experiments/results')
b0=[float(row['m1_p50_ms']) for s in [0,1,2] for row in csv.DictReader(open(r/f'main_seed{s}.csv')) if row['baseline']=='B0']
b2=[float(row['m1_p50_ms']) for s in [0,1,2] for row in csv.DictReader(open(r/f'main_seed{s}.csv')) if row['baseline']=='B2']
ok=sum(b2)/len(b2)<=sum(b0)/len(b0)
print('B2 mean p50',round(sum(b2)/len(b2),2),'B0 mean p50',round(sum(b0)/len(b0),2),'gate',ok)
m6=sum(1 for _ in open(r/'franka_m6_rtt.csv'))-1
print('M6 rows',m6,'expect 50')
"

echo "--- artifacts ---"
for f in \
  doctor/paper1/figures/fig1_system_overview.svg \
  doctor/paper1/figures/fig_iqa_hist.pdf \
  doctor/paper1/experiments/results/recommended_tau.json \
  franka_api_server/franka_api_server/skills/poses.yaml
  doctor/paper1/experiments/logs/run_001.jsonl
  doctor/paper1/figures/fig2_routing_flow.pdf
  doctor/paper1/experiments/results/main_seed0.csv
  doctor/paper1/figures/fig5_rtt_cdf.pdf
  doctor/paper1/figures/fig6_valid_rate.pdf
  doctor/paper1/experiments/results/franka_m6_rtt.csv
  doctor/paper1/figures/fig_s1_franka_rtt.pdf; do
  if [[ -f "$f" ]]; then echo "OK $f"; else echo "MISSING $f"; fi
done

echo "--- phase 5 draft pdf ---"
if [[ -f "${PAPER1_ROOT}/latex/main.pdf" ]]; then
  echo "OK main.pdf $(wc -c < "${PAPER1_ROOT}/latex/main.pdf") bytes"
else
  bash scripts/paper1_build_draft.sh 2>&1 | tail -5
fi

echo "========== Done. Log: ${LOG} =========="
