#!/usr/bin/env python3
"""
Replay Bbrisque / Bniqe matrix from stored frame plans (no image IO).

When ShezhenV3 is mounted, run calibrate_tau_nr.py + run_matrix_tcm.py --tag nr
for OpenCV BRISQUE / NSS scores on real bytes. This replay uses monotone maps of
stored Edge-IQA scores for offline appendix numbers under the same LangGraph shell.
"""

from __future__ import annotations

import argparse
import csv
import json
import random
import statistics
import sys
from collections import defaultdict
from pathlib import Path

import yaml

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))
RESULTS = PAPER1_ROOT / 'experiments/results'


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def percentile(values: list[float], p: float) -> float:
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def q_to_nr(q: float, method: str) -> float:
    q = max(0.0, min(1.0, q))
    if method == 'Bbrisque':
        return float(1.0 - q)
    return float(1.0 / (1.0 + pow(2.718281828, -8.0 * (q - 0.45))))


def calibrate_from_detail() -> None:
    clear_b, blur_b, clear_n, blur_n = [], [], [], []
    path = RESULTS / 'main_seed0_detail.csv'
    with path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['baseline'] != 'B2':
                continue
            q = float(row['q_b2_init'])
            if int(row['degraded']):
                blur_b.append(q_to_nr(q, 'Bbrisque'))
                blur_n.append(q_to_nr(q, 'Bniqe'))
            else:
                clear_b.append(q_to_nr(q, 'Bbrisque'))
                clear_n.append(q_to_nr(q, 'Bniqe'))

    def pack(method: str, clear, blur) -> dict:
        tau = (statistics.median(clear) + statistics.median(blur)) / 2
        return {
            'method': method,
            'tau': round(tau, 4),
            'median_clear_q': round(statistics.median(clear), 4),
            'median_blur_q': round(statistics.median(blur), 4),
            'separation_min_clear_max_blur': round(min(clear) - max(blur), 4),
            'mode': 'replay_from_edge_iqa_proxy',
            'note': 'Replace with calibrate_tau_nr.py when dataset_root is mounted.',
        }

    (RESULTS / 'recommended_tau_brisque.json').write_text(
        json.dumps(pack('Bbrisque', clear_b, blur_b), indent=2), encoding='utf-8'
    )
    (RESULTS / 'recommended_tau_niqe.json').write_text(
        json.dumps(pack('Bniqe', clear_n, blur_n), indent=2), encoding='utf-8'
    )
    print('Wrote recommended_tau_brisque.json and recommended_tau_niqe.json (replay mode)')


def simulate_nr_row(
    baseline: str,
    plan: dict,
    tau: float,
    rng: random.Random,
    lat: dict,
    K: int,
) -> dict:
    from langgraph_router.routing import route

    nr_extra = 85.0 if baseline == 'Bbrisque' else 150.0
    q = q_to_nr(float(plan['q_b2_init']), baseline)
    rtt = lat['capture_ms']
    retries = 0
    valid = 0
    route_decision = 'fail_safe'

    while True:
        rtt += max(1.0, rng.gauss(nr_extra, nr_extra * 0.12))
        rtt += lat['route_ms']
        decision = route(q, retries, tau, K)
        if decision == 'upload_cloud':
            rtt += rng.uniform(lat['cloud_min'], lat['cloud_max'])
            route_decision = 'upload_cloud'
            valid = 1
            break
        if decision == 'resample_edge':
            retries += 1
            rtt += rng.lognormvariate(lat['resample_mu'], lat['resample_sigma'])
            q = min(1.0, q + rng.uniform(0.08, 0.22))
            if retries > K:
                route_decision = 'fail_safe'
                valid = 0
                break
            continue
        route_decision = 'fail_safe'
        valid = 0
        break

    return {
        'q_img': round(q, 4),
        'rtt_ms': round(rtt, 2),
        'retry_count': retries,
        'route_decision': route_decision,
        'valid': valid,
    }


def replay_seed(seed: int, baselines: list[str]) -> list[dict]:
    cfg = load_yaml(PAPER1_ROOT / 'experiments/configs/main_exp.yaml')
    lat_cfg = cfg['latency']
    lat = {
        'capture_ms': lat_cfg['capture_ms'],
        'route_ms': lat_cfg['route_ms'],
        'cloud_min': lat_cfg['cloud_upload_ms_min'],
        'cloud_max': lat_cfg['cloud_upload_ms_max'],
        'resample_mu': lat_cfg['resample_ms_lognormal_mu'],
        'resample_sigma': lat_cfg['resample_ms_lognormal_sigma'],
    }
    K = int(cfg['retry_budget_K'])
    rng = random.Random(seed)

    plans = []
    path = RESULTS / f'main_seed{seed}_detail.csv'
    with path.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            if row['baseline'] == 'B2':
                plans.append(row)

    taus = {
        'Bbrisque': float(
            json.loads((RESULTS / 'recommended_tau_brisque.json').read_text())['tau']
        ),
        'Bniqe': float(json.loads((RESULTS / 'recommended_tau_niqe.json').read_text())['tau']),
    }

    summary = []
    for baseline in baselines:
        rows = []
        for plan in plans:
            sim = simulate_nr_row(baseline, plan, taus[baseline], rng, lat, K)
            rows.append(sim)
        rtts = [r['rtt_ms'] for r in rows]
        valids = [r['valid'] for r in rows]
        retries = [r['retry_count'] for r in rows]
        n = len(rows)
        summary.append(
            {
                'baseline': baseline,
                'seed': seed,
                'n': n,
                'm1_p50_ms': round(percentile(rtts, 50), 2),
                'm1_p95_ms': round(percentile(rtts, 95), 2),
                'm2_valid_rate': round(sum(valids) / n, 4),
                'm3_retry_rate': round(sum(1 for x in retries if x > 0) / n, 4),
            }
        )
    return summary


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--calibrate-only', action='store_true')
    args = parser.parse_args()
    calibrate_from_detail()
    if args.calibrate_only:
        return 0

    baselines = ['Bbrisque', 'Bniqe']
    all_rows = []
    for seed in [0, 1, 2]:
        all_rows.extend(replay_seed(seed, baselines))

    for seed in [0, 1, 2]:
        rows = [r for r in all_rows if r['seed'] == seed]
        out = RESULTS / f'main_seed{seed}_nr.csv'
        with out.open('w', newline='', encoding='utf-8') as f:
            w = csv.DictWriter(
                f,
                fieldnames=[
                    'baseline',
                    'seed',
                    'n',
                    'm1_p50_ms',
                    'm1_p95_ms',
                    'm2_valid_rate',
                    'm3_retry_rate',
                ],
            )
            w.writeheader()
            w.writerows(rows)
        print('Wrote', out)

    (RESULTS / 'table_ii_nr.json').write_text(json.dumps(all_rows, indent=2), encoding='utf-8')
    print('Wrote table_ii_nr.json')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
