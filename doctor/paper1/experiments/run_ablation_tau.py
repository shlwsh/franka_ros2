#!/usr/bin/env python3
"""M4: sweep τ for B2, output ablation_tau.csv."""

from __future__ import annotations

import argparse
import csv
import random
import sys
from pathlib import Path

import yaml

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from experiments.run_matrix import aggregate_metrics, simulate_frame
from sim.latency_model import LatencyConfig
from paper1_trace import init_trace, log_progress, trace_call


@trace_call()
def main() -> int:
    init_trace(__file__)
    import logging

    log = logging.getLogger('paper1.run_ablation_tau')
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default='experiments/configs/ablation_tau.yaml')
    args = parser.parse_args()

    cfg_path = PAPER1_ROOT / args.config
    cfg = yaml.safe_load(cfg_path.read_text(encoding='utf-8'))
    lat_cfg = cfg['latency']
    lat = LatencyConfig(
        capture_ms=lat_cfg['capture_ms'],
        edge_iqa_ms_mean=lat_cfg['edge_iqa_ms_mean'],
        edge_iqa_ms_std=lat_cfg['edge_iqa_ms_std'],
        route_ms=lat_cfg['route_ms'],
        resample_mu=lat_cfg['resample_ms_lognormal_mu'],
        resample_sigma=lat_cfg['resample_ms_lognormal_sigma'],
        cloud_min=lat_cfg['cloud_upload_ms_min'],
        cloud_max=lat_cfg['cloud_upload_ms_max'],
    )

    seed = int(cfg['seeds'][0])
    n_frames = int(cfg['n_frames_per_baseline'])
    rows = []
    tau_values = cfg['tau_values']
    log.info('tau sweep n_tau=%s n_frames=%s seed=%s', len(tau_values), n_frames, seed)

    for t_idx, tau in enumerate(tau_values, start=1):
        rng = random.Random(seed + int(tau * 1000))
        run_cfg = {**cfg, 'tau': float(tau)}
        frame_rows = []
        for f_idx in range(n_frames):
            q, rtt, retry, rd, valid = simulate_frame('B2', rng, run_cfg, lat)
            frame_rows.append(
                {
                    'tau': tau,
                    'q_img': q,
                    'rtt_ms': rtt,
                    'retry_count': retry,
                    'route_decision': rd,
                    'valid': valid,
                }
            )
            log_progress(log, f_idx + 1, n_frames, every=100, label=f'tau={tau}')
        m = aggregate_metrics(
            [
                {
                    'rtt_ms': r['rtt_ms'],
                    'valid': r['valid'],
                    'retry_count': r['retry_count'],
                }
                for r in frame_rows
            ]
        )
        rows.append({'tau': tau, 'seed': seed, **m})
        log.info('tau=%s metrics=%s (%s/%s)', tau, m, t_idx, len(tau_values))

    out = PAPER1_ROOT / 'experiments/results/ablation_tau.csv'
    out.parent.mkdir(parents=True, exist_ok=True)
    fields = ['tau', 'seed', 'n', 'm1_p50_ms', 'm1_p95_ms', 'm2_valid_rate', 'm3_retry_rate']
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)
    print(f'Wrote {out} ({len(rows)} rows)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
