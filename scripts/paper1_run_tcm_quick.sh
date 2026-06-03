#!/usr/bin/env bash
# Quick Paper I validation (~2-5 min): small val + 80 frames x 1 seed
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"

QUICK_CFG=experiments/configs/main_exp_quick.yaml
MAX_VAL=120
TAG=quick

echo "=== [quick 1/5] Tau B2 (max-val=$MAX_VAL) ==="
python3 experiments/edge_iqa/calibrate_tau_tcm.py --max-val "$MAX_VAL"

echo "=== [quick 2/5] Tau B3 (max-val=$MAX_VAL) ==="
if [[ ! -f experiments/results/b3_mobilenet.pt ]]; then
  echo "B3 checkpoint missing; train with --max-train 400 first or run full pipeline"
  exit 1
fi
.venv/bin/python experiments/edge_iqa/calibrate_tau_b3.py --max-val "$MAX_VAL"

echo "=== [quick 3/5] Unit tests ==="
python3 -m pytest tests/test_resample_physics.py tests/test_routing.py -q

echo "=== [quick 4/5] Main matrix (quick config, tag=$TAG) ==="
.venv/bin/python experiments/run_matrix_tcm.py \
  --config "$QUICK_CFG" \
  --tag "$TAG"

echo "=== [quick 5/5] Summary JSON ==="
python3 - <<'PY'
import csv, json, statistics
from pathlib import Path

root = Path('experiments/results')
rows = list(csv.DictReader((root / 'main_seed0.csv').open()))
summary = {}
for r in rows:
    bl = r['baseline']
    summary[bl] = {
        'm1_p50_ms': float(r['m1_p50_ms']),
        'm2_valid_rate': float(r['m2_valid_rate']),
        'm3_retry_rate': float(r['m3_retry_rate']),
    }
meta = json.loads((root / 'table_ii_quick_meta.json').read_text())
out = {
    'mode': 'quick',
    'n_frames': meta.get('n_frames_per_baseline'),
    'seeds': meta.get('seeds'),
    'tau_b2': meta.get('tau_b2'),
    'tau_b3': meta.get('tau_b3'),
    'resample_model': meta.get('resample_model'),
    'baselines': summary,
}
path = root / 'quick_summary.json'
path.write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
print(f'Wrote {path}')
PY

echo "Done. Quick results: experiments/results/quick_summary.json"
echo "Full validation: bash scripts/paper1_run_tcm_full.sh"
