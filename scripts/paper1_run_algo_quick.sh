#!/usr/bin/env bash
# Algorithm enhancement quick validation (B2 vs B2d/B2m/B2u) — ~1–3 min
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT/doctor/paper1"

CFG=experiments/configs/main_exp_algo_quick.yaml
TAG=algo_quick

echo "=== [algo 1/3] Unit tests ==="
python3 -m pytest tests/test_algo_enhance.py tests/test_resample_physics.py tests/test_routing.py -q

echo "=== [algo 2/3] Ablation matrix (B2/B2d/B2m/B2u) ==="
python3 experiments/run_matrix_tcm.py --config "$CFG" --tag "$TAG"

echo "=== [algo 3/3] Summary ==="
python3 - <<'PY'
import csv, json
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
meta = json.loads((root / 'table_ii_algo_quick_meta.json').read_text())
out = {
    'mode': 'algo_quick',
    'n_frames': meta.get('n_frames_per_baseline'),
    'baselines': summary,
    'algo_config': 'experiments/configs/algo_enhance.yaml',
}
path = root / 'algo_quick_summary.json'
path.write_text(json.dumps(out, indent=2), encoding='utf-8')
print(json.dumps(out, indent=2))
print(f'Wrote {path}')
PY

echo "Done. See experiments/results/algo_quick_summary.json"
