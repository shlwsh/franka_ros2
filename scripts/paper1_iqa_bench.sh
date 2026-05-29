#!/usr/bin/env bash
# Benchmark POST /vision/evaluate latency (phase 2)
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PAPER1_ROOT="${PAPER1_ROOT:-${ROOT}/doctor/paper1}"
FRANKA_API_BASE="${FRANKA_API_BASE:-http://127.0.0.1:8000/api/v1}"
FRANKA_API_KEY="${FRANKA_API_KEY:-franka-api-default-key}"
N="${BENCH_N:-50}"
OUT="${ROOT}/doctor/paper1/experiments/edge_iqa/api_latency_benchmark.json"

IMG="${PAPER1_ROOT}/experiments/synthetic/clear/clear_0000.png"
if [[ ! -f "$IMG" ]]; then
  echo "生成合成数据..."
  python3 "${PAPER1_ROOT}/scripts/synth_degrade.py"
fi

if ! curl -sf "${FRANKA_API_BASE}/status/joints?api_key=${FRANKA_API_KEY}" -o /dev/null; then
  echo "错误: API 未启动，请先运行 scripts/testall.sh"
  exit 1
fi

echo "Benchmark vision/evaluate n=${N} ..."
python3 - "$IMG" "$N" "$FRANKA_API_BASE" "$FRANKA_API_KEY" "$OUT" <<'PY'
import json
import sys
import time
import urllib.request
from pathlib import Path

img_path, n, base, key, out = sys.argv[1:6]
n = int(n)
data = Path(img_path).read_bytes()

samples = []
for _ in range(n):
    boundary = "----benchboundary"
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="bench.png"\r\n'
        f"Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        f"{base.rstrip('/')}/vision/evaluate?api_key={key}",
        data=body,
        method="POST",
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    )
    t0 = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as resp:
        resp.read()
    samples.append((time.perf_counter() - t0) * 1000.0)

def pct(vals, p):
    s = sorted(vals)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    return s[f] if f == c else s[f] + (s[c] - s[f]) * (k - f)

report = {
    "n": n,
    "p50_ms": round(pct(samples, 50), 3),
    "p95_ms": round(pct(samples, 95), 3),
    "mean_ms": round(sum(samples) / len(samples), 3),
    "pass_p95_under_35ms": pct(samples, 95) < 35.0,
}
Path(out).parent.mkdir(parents=True, exist_ok=True)
Path(out).write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(report, indent=2))
PY

echo "Wrote $OUT"
