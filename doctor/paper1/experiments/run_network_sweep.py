#!/usr/bin/env python3
"""Network perturbation sweep: RTT x packet loss x baseline (Paper I §2.1)."""

from __future__ import annotations

import argparse
import copy
import csv
import json
import sys
from pathlib import Path

import yaml

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from experiments.run_matrix_tcm import (  # noqa: E402
    DEFAULT_CFG,
    PHYSICS_CFG,
    TCM_CFG,
    load_physics_cfg,
    load_yaml,
    run_seed,
)

DEFAULT_SWEEP_CFG = PAPER1_ROOT / 'experiments/configs/network_sweep_quick.yaml'


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=str(DEFAULT_SWEEP_CFG))
    parser.add_argument('--tcm-config', type=str, default=str(TCM_CFG))
    parser.add_argument('--physics-config', type=str, default=str(PHYSICS_CFG))
    parser.add_argument('--tag', type=str, default='quick')
    parser.add_argument('--seed', type=int, default=0)
    args = parser.parse_args()

    sweep_cfg = load_yaml(Path(args.config))
    base_cfg = load_yaml(DEFAULT_CFG)
    tcm_cfg = load_yaml(Path(args.tcm_config))
    physics_cfg = load_physics_cfg(Path(args.physics_config))

    test_json = PAPER1_ROOT / 'experiments/splits/tcm_test.json'
    if not test_json.is_file():
        raise SystemExit(f'missing {test_json}')
    test_entries = json.loads(test_json.read_text(encoding='utf-8'))

    rtt_grid = [float(x) for x in sweep_cfg.get('cloud_rtt_ms_grid', [50, 300])]
    loss_grid = [float(x) for x in sweep_cfg.get('packet_loss_grid', [0.0, 0.1])]
    baselines = list(sweep_cfg.get('baselines', ['B2', 'B2d']))
    n_frames = int(sweep_cfg.get('n_frames_per_baseline', 40))

    results_dir = PAPER1_ROOT / 'experiments' / 'results'
    rows: list[dict] = []

    total = len(rtt_grid) * len(loss_grid)
    step = 0
    for cloud_rtt in rtt_grid:
        for p_loss in loss_grid:
            step += 1
            cfg = copy.deepcopy(base_cfg)
            cfg.update({k: v for k, v in sweep_cfg.items() if k not in ('cloud_rtt_ms_grid', 'packet_loss_grid')})
            cfg['n_frames_per_baseline'] = n_frames
            cfg['baselines'] = baselines
            lat = dict(cfg.get('latency', {}))
            lat['cloud_upload_ms_min'] = cloud_rtt
            lat['cloud_upload_ms_max'] = cloud_rtt
            lat['packet_loss_fixed'] = p_loss
            lat['packet_loss_max'] = p_loss
            cfg['latency'] = lat
            if sweep_cfg.get('algo_enhance_config'):
                cfg['algo_enhance_config'] = sweep_cfg['algo_enhance_config']
            if 'b3_use_learned' in sweep_cfg:
                cfg['b3_use_learned'] = sweep_cfg['b3_use_learned']

            _, summary = run_seed(
                cfg, tcm_cfg, physics_cfg, test_entries, args.seed, baselines
            )
            for s in summary:
                row = {
                    'cloud_rtt_ms': cloud_rtt,
                    'packet_loss': p_loss,
                    'baseline': s['baseline'],
                    'seed': s['seed'],
                    'n': s['n'],
                    'm1_p50_ms': s['m1_p50_ms'],
                    'm1_p95_ms': s['m1_p95_ms'],
                    'm2_valid_rate': s['m2_valid_rate'],
                    'm3_retry_rate': s['m3_retry_rate'],
                }
                rows.append(row)
            print(
                f'[{step}/{total}] rtt={cloud_rtt}ms loss={p_loss} '
                f"B2 M2={next(x['m2_valid_rate'] for x in summary if x['baseline']=='B2'):.3f} "
                f"B2d M2={next(x['m2_valid_rate'] for x in summary if x['baseline']=='B2d'):.3f}"
            )

    tag = args.tag.strip() or 'quick'
    json_path = results_dir / f'network_sweep_{tag}.json'
    csv_path = results_dir / f'network_sweep_{tag}.csv'
    meta = {
        'mode': tag,
        'cloud_rtt_ms_grid': rtt_grid,
        'packet_loss_grid': loss_grid,
        'baselines': baselines,
        'n_frames_per_cell': n_frames,
        'seed': args.seed,
        'n_cells': total,
    }
    payload = {'meta': meta, 'rows': rows}
    json_path.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    fieldnames = list(rows[0].keys()) if rows else []
    with csv_path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {json_path} ({len(rows)} rows)')
    print(f'Wrote {csv_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
