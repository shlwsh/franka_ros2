#!/usr/bin/env python3
"""Offline main experiment using real ShezhenV3 test images + Edge-IQA scores."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from io import BytesIO
from pathlib import Path
from typing import Dict, List, Tuple

import yaml
from PIL import Image, ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.coco_roi import bbox_from_entry
from edge_iqa.learned_b3 import get_learned_scorer
from langgraph_router.routing import route
from sim.latency_model import LatencyConfig, sample_cloud_upload_ms, sample_edge_iqa_ms, sample_resample_ms

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/main_exp.yaml'
TCM_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def load_tau() -> float:
    tau_file = PAPER1_ROOT / 'experiments/results/recommended_tau.json'
    if tau_file.is_file():
        return float(json.loads(tau_file.read_text(encoding='utf-8'))['tau'])
    return 0.505


def blur_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def score_image_b2(
    data: bytes,
    entry: dict,
    *,
    use_roi: bool,
    roi_padding: float,
) -> float:
    from edge_iqa.scorer import compute_q_from_bytes

    bboxes = bbox_from_entry(entry)
    return float(
        compute_q_from_bytes(
            data,
            bboxes=bboxes,
            use_roi=use_roi,
            roi_padding=roi_padding,
        ).q_img
    )


def score_image_b3(data: bytes, entry: dict, cfg: dict) -> float:
    bboxes = bbox_from_entry(entry)
    ckpt = PAPER1_ROOT / cfg.get('b3_checkpoint', 'experiments/results/b3_mobilenet.pt')
    if cfg.get('b3_use_learned', True) and ckpt.is_file():
        return float(get_learned_scorer(ckpt).score_bytes(data, bboxes=bboxes).q_img)
    from edge_iqa.scorer import compute_q_from_bytes

    q = float(
        compute_q_from_bytes(
            data,
            bboxes=bboxes,
            use_roi=bool(cfg.get('use_roi', True)),
            roi_padding=float(cfg.get('roi_padding', 0.08)),
        ).q_img
    )
    return min(1.0, q + float(cfg.get('b3_q_boost', 0.08)))


def simulate_frame(
    baseline: str,
    q: float,
    rng: random.Random,
    cfg: dict,
    lat: LatencyConfig,
    tau: float,
    K: int,
) -> Tuple[float, float, int, str, int]:
    if baseline == 'B3':
        pass  # q already from learned B3 scorer in frame plan

    rtt = lat.capture_ms
    retries = 0
    final_route = 'fail_safe'
    valid = 0

    if baseline == 'B0':
        rtt += sample_cloud_upload_ms(rng, lat)
        if q < tau:
            rtt += rng.uniform(
                float(cfg.get('b0_bad_upload_penalty_min', 120)),
                float(cfg.get('b0_bad_upload_penalty_max', 220)),
            )
        final_route = 'upload_cloud'
        valid = 1 if q >= tau else 0
        return q, rtt, retries, final_route, valid

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


def run_seed(
    cfg: dict,
    tcm_cfg: dict,
    test_entries: list,
    seed: int,
    baselines: List[str] | None,
) -> Tuple[List[dict], List[dict]]:
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
    tau = load_tau()
    K = int(cfg['retry_budget_K'])
    rng = random.Random(seed)
    n_frames = int(cfg.get('n_frames_per_baseline', 500))
    n_frames = min(n_frames, len(test_entries))
    bl_list = baselines or cfg['baselines']

    r_min = float(tcm_cfg.get('blur_radius_min', 2.5))
    r_max = float(tcm_cfg.get('blur_radius_max', 5.0))
    use_roi = bool(tcm_cfg.get('use_roi', True))
    roi_padding = float(tcm_cfg.get('roi_padding', 0.08))
    merged_cfg = {**cfg, **tcm_cfg}

    indices = list(range(len(test_entries)))
    rng.shuffle(indices)
    frame_plan = []
    for i in range(n_frames):
        entry = test_entries[indices[i % len(indices)]]
        path = Path(entry['path'])
        raw = path.read_bytes()
        if rng.random() < 0.5:
            q_b2 = score_image_b2(raw, entry, use_roi=use_roi, roi_padding=roi_padding)
            q_b3 = score_image_b3(raw, entry, merged_cfg)
            degraded = False
        else:
            radius = rng.uniform(r_min, r_max)
            blurred = blur_bytes(raw, radius)
            q_b2 = score_image_b2(blurred, entry, use_roi=use_roi, roi_padding=roi_padding)
            q_b3 = score_image_b3(blurred, entry, merged_cfg)
            degraded = True
        frame_plan.append(
            {
                'entry': entry,
                'q_b2': q_b2,
                'q_b3': q_b3,
                'degraded': degraded,
            }
        )

    detail_rows: List[dict] = []
    summary_rows: List[dict] = []

    for baseline in bl_list:
        frame_rows = []
        for fid, plan in enumerate(frame_plan):
            q_init = plan['q_b3'] if baseline == 'B3' else plan['q_b2']
            q, rtt, retry, rd, valid = simulate_frame(
                baseline, q_init, rng, cfg, lat, tau, K
            )
            row = {
                'baseline': baseline,
                'seed': seed,
                'frame_id': fid,
                'q_img': round(q, 4),
                'q_init': round(q_init, 4),
                'q_b2': round(plan['q_b2'], 4),
                'q_b3': round(plan['q_b3'], 4),
                'degraded': int(plan['degraded']),
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
    parser.add_argument('--config', type=str, default=str(DEFAULT_CFG))
    parser.add_argument('--tcm-config', type=str, default=str(TCM_CFG))
    parser.add_argument('--baseline', type=str, default='')
    parser.add_argument('--seed', type=int, default=-1)
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))
    tcm_cfg = load_yaml(Path(args.tcm_config))
    test_json = PAPER1_ROOT / 'experiments/splits/tcm_test.json'
    if not test_json.is_file():
        raise SystemExit(f'missing {test_json}; run import_shezhenv3.py first')
    test_entries = json.loads(test_json.read_text(encoding='utf-8'))

    seeds = cfg['seeds'] if args.seed < 0 else [args.seed]
    baselines = [args.baseline] if args.baseline else None
    results_dir = PAPER1_ROOT / 'experiments' / 'results'
    all_summary: List[dict] = []

    for seed in seeds:
        detail, summary = run_seed(cfg, tcm_cfg, test_entries, seed, baselines)
        write_csv(
            results_dir / f'main_seed{seed}_detail.csv',
            detail,
            [
                'baseline',
                'seed',
                'frame_id',
                'q_img',
                'q_init',
                'q_b2',
                'q_b3',
                'degraded',
                'rtt_ms',
                'retry_count',
                'route_decision',
                'valid',
            ],
        )
        write_csv(
            results_dir / f'main_seed{seed}.csv',
            summary,
            ['baseline', 'seed', 'n', 'm1_p50_ms', 'm1_p95_ms', 'm2_valid_rate', 'm3_retry_rate'],
        )
        all_summary.extend(summary)
        print(f'seed {seed}: {len(detail)} detail rows, tau={load_tau()}')

    table_path = results_dir / 'table_ii.json'
    table_path.write_text(json.dumps(all_summary, indent=2), encoding='utf-8')
    meta = {
        'dataset': 'shezhenv3-coco',
        'split': 'test',
        'n_test_images': len(test_entries),
        'tau': load_tau(),
        'seeds': seeds,
        'use_roi': bool(tcm_cfg.get('use_roi', True)),
        'b3_use_learned': bool(cfg.get('b3_use_learned', True)),
    }
    (results_dir / 'table_ii_meta.json').write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'Table II data -> {table_path}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
