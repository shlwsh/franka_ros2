#!/usr/bin/env bash
# Network perturbation quick sweep (RTT x packet_loss x B2/B2d) — ~2–4 min
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"

echo "=== Network sweep quick (B2 vs B2d) ==="
python3 experiments/run_network_sweep.py --tag quick

echo "=== Summary highlight ==="
python3 - <<'PY'
import json
from pathlib import Path

data = json.loads((Path('experiments/results/network_sweep_quick.json')).read_text())
rows = data['rows']
# B2: M2 不随网络变化（固定 τ 未感知 P_loss）
# B2d: M2 随 P_loss 下降（τ_t 升高 → 更保守）
by_loss = {}
for r in rows:
    if r['baseline'] != 'B2d':
        continue
    key = r['packet_loss']
    by_loss.setdefault(key, []).append(r['m2_valid_rate'])
print('B2d M2 vs packet_loss (avg over RTT grid):')
for loss in sorted(by_loss):
    avg = sum(by_loss[loss]) / len(by_loss[loss])
    print(f'  P_loss={loss:.2f} -> M2={avg:.3f}')
print('CSV: experiments/results/network_sweep_quick.csv')
PY

echo "Done."
