#!/usr/bin/env python3
"""Offline main experiment matrix: baselines B0-B3, metrics M1-M3."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from pathlib import Path
from typing import Dict, List, Tuple

import yaml

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from langgraph_router.routing import route
from sim.latency_model import LatencyConfig, sample_cloud_upload_ms, sample_edge_iqa_ms, sample_resample_ms


def load_config(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def sample_q_img(rng: random.Random, cfg: dict) -> float:
    qcfg = cfg['quality']
    if rng.random() < qcfg['clear_fraction']:
        q = rng.gauss(qcfg['clear_q_mean'], qcfg['clear_q_std'])
    else:
        q = rng.gauss(qcfg['blur_q_mean'], qcfg['blur_q_std'])
    return max(0.0, min(1.0, q))


def simulate_frame(
    baseline: str,
    rng: random.Random,
    cfg: dict,
    lat: LatencyConfig,
) -> Tuple[float, float, int, str, int]:
    """Return q_img, rtt_ms, retry_count, route_decision, valid(0/1)."""
    tau = float(cfg['tau'])
    K = int(cfg['retry_budget_K'])
    q = sample_q_img(rng, cfg)
    if baseline == 'B3':
        q = min(1.0, q + float(cfg.get('b3_q_boost', 0.08)))

    rtt = lat.capture_ms
    retries = 0
    final_route = 'fail_safe'
    valid = 0

    if baseline == 'B0':
        rtt += sample_cloud_upload_ms(rng, lat)
        if q < tau:
            # Naive upload: cloud still processes a bad frame (wasted RTT, M2=0)
            rtt += rng.uniform(
                float(cfg.get('b0_bad_upload_penalty_min', 120)),
                float(cfg.get('b0_bad_upload_penalty_max', 220)),
            )
        final_route = 'upload_cloud'
        valid = 1 if q >= tau else 0
        return q, rtt, retries, final_route, valid

    # B1+ use edge IQA
    while True:
        rtt += sample_edge_iqa_ms(rng, lat)

        if baseline == 'B1':
            rtt += lat.route_ms
            rtt += sample_cloud_upload_ms(rng, lat)
            final_route = 'upload_cloud'
            valid = 1 if q >= tau else 0
            break

        rtt += lat.route_ms
        decision = route(q, retries, tau, K)

        if decision == 'upload_cloud':
            rtt += sample_cloud_upload_ms(rng, lat)
            final_route = 'upload_cloud'
            valid = 1
            break
        if decision == 'resample_edge':
            retries += 1
            rtt += sample_resample_ms(rng, lat)
            q = min(1.0, q + rng.uniform(0.15, 0.35))
            if retries > K:
                final_route = 'fail_safe'
                valid = 0
                break
            continue
        final_route = 'fail_safe'
        valid = 0
        break

    return q, rtt, retries, final_route, valid


def percentile(values: List[float], p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def aggregate_metrics(rows: List[dict]) -> Dict[str, float]:
    rtts = [r['rtt_ms'] for r in rows]
    valids = [r['valid'] for r in rows]
    retries = [r['retry_count'] for r in rows]
    n = len(rows)
    return {
        'm1_p50_ms': round(percentile(rtts, 50), 2),
        'm1_p95_ms': round(percentile(rtts, 95), 2),
        'm2_valid_rate': round(sum(valids) / n, 4) if n else 0.0,
        'm3_retry_rate': round(sum(1 for x in retries if x > 0) / n, 4) if n else 0.0,
        'n': n,
    }


def run_seed(cfg: dict, seed: int, baselines: List[str] | None) -> Tuple[List[dict], List[dict]]:
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
    rng = random.Random(seed)
    n_frames = int(cfg['n_frames_per_baseline'])
    bl_list = baselines or cfg['baselines']
    detail_rows: List[dict] = []
    summary_rows: List[dict] = []

    for baseline in bl_list:
        frame_rows = []
        for fid in range(n_frames):
            q, rtt, retry, rd, valid = simulate_frame(baseline, rng, cfg, lat)
            row = {
                'baseline': baseline,
                'seed': seed,
                'frame_id': fid,
                'q_img': round(q, 4),
                'rtt_ms': round(rtt, 2),
                'retry_count': retry,
                'route_decision': rd,
                'valid': valid,
            }
            frame_rows.append(row)
            detail_rows.append(row)
        summary_rows.append({'baseline': baseline, 'seed': seed, **aggregate_metrics(frame_rows)})

    return detail_rows, summary_rows


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default='experiments/configs/main_exp.yaml')
    parser.add_argument('--baseline', type=str, default='')
    parser.add_argument('--seed', type=int, default=-1)
    args = parser.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.is_absolute():
        cfg_path = PAPER1_ROOT / cfg_path
    cfg = load_config(cfg_path)

    seeds = cfg['seeds'] if args.seed < 0 else [args.seed]
    baselines = [args.baseline] if args.baseline else None

    results_dir = PAPER1_ROOT / 'experiments' / 'results'
    all_summary: List[dict] = []

    for seed in seeds:
        detail, summary = run_seed(cfg, seed, baselines)
        write_csv(
            results_dir / f'main_seed{seed}_detail.csv',
            detail,
            ['baseline', 'seed', 'frame_id', 'q_img', 'rtt_ms', 'retry_count', 'route_decision', 'valid'],
        )
        write_csv(
            results_dir / f'main_seed{seed}.csv',
            summary,
            ['baseline', 'seed', 'n', 'm1_p50_ms', 'm1_p95_ms', 'm2_valid_rate', 'm3_retry_rate'],
        )
        all_summary.extend(summary)
        print(f'seed {seed}: wrote {len(detail)} detail rows, {len(summary)} summary rows')

    table_path = results_dir / 'table_ii.json'
    table_path.write_text(json.dumps(all_summary, indent=2), encoding='utf-8')
    print(f'Table II data -> {table_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
