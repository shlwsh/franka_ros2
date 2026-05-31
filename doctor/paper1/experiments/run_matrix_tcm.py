#!/usr/bin/env python3
"""Offline main experiment: ShezhenV3 test + physical resample + Hybrid B4."""

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
from edge_iqa.scorer import compute_q_from_bytes
from langgraph_router.dynamic_tau import dynamic_tau
from langgraph_router.hybrid_route import hybrid_gate
from langgraph_router.multi_frame_iqa import fuse_burst_scores, simulate_burst_scores
from langgraph_router.routing import route
from langgraph_router.utility_route import utility_route
from sim.latency_model import LatencyConfig, sample_cloud_upload_ms, sample_edge_iqa_ms, sample_resample_ms
from sim.resample_physics import apply_resample_transform, load_physics_cfg
from paper1_trace import init_trace, log_progress, trace_call

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/main_exp.yaml'
TCM_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'
PHYSICS_CFG = PAPER1_ROOT / 'experiments/configs/resample_physics.yaml'
ALGO_CFG = PAPER1_ROOT / 'experiments/configs/algo_enhance.yaml'


def load_yaml(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def load_tau_b2() -> float:
    path = PAPER1_ROOT / 'experiments/results/recommended_tau.json'
    if path.is_file():
        return float(json.loads(path.read_text(encoding='utf-8'))['tau'])
    return 0.465


def load_tau_b3() -> float:
    path = PAPER1_ROOT / 'experiments/results/recommended_tau_b3.json'
    if path.is_file():
        return float(json.loads(path.read_text(encoding='utf-8'))['tau'])
    return 0.55


def blur_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def score_b2(data: bytes, entry: dict, *, use_roi: bool, roi_padding: float) -> Tuple[float, List[str]]:
    bboxes = bbox_from_entry(entry)
    r = compute_q_from_bytes(
        data,
        bboxes=bboxes,
        use_roi=use_roi,
        roi_padding=roi_padding,
    )
    return float(r.q_img), list(r.flags)


def score_b3(data: bytes, entry: dict, cfg: dict) -> float:
    bboxes = bbox_from_entry(entry)
    ckpt = PAPER1_ROOT / cfg.get('b3_checkpoint', 'experiments/results/b3_mobilenet.pt')
    if cfg.get('b3_use_learned', True) and ckpt.is_file():
        return float(get_learned_scorer(ckpt).score_bytes(data, bboxes=bboxes).q_img)
    q, _ = score_b2(
        data,
        entry,
        use_roi=bool(cfg.get('use_roi', True)),
        roi_padding=float(cfg.get('roi_padding', 0.08)),
    )
    return min(1.0, q + float(cfg.get('b3_q_boost', 0.08)))


def load_algo_cfg(path: Path | None = None) -> dict:
    p = path or ALGO_CFG
    if p.is_file():
        return load_yaml(p)
    return {}


def resolve_decision(
    baseline: str,
    q_gate: float,
    retries: int,
    tau: float,
    K: int,
    rtt: float,
    rng: random.Random,
    algo_cfg: dict,
    lat_cfg: dict,
) -> str:
    if baseline == 'B2d':
        dt = algo_cfg.get('dynamic_tau', {})
        fixed_loss = lat_cfg.get('packet_loss_fixed')
        if fixed_loss is not None:
            p_loss = float(fixed_loss)
        else:
            p_loss = rng.uniform(0.0, float(lat_cfg.get('packet_loss_max', 0.15)))
        tau = dynamic_tau(
            tau,
            rtt,
            p_loss,
            alpha=float(dt.get('alpha', 0.08)),
            beta=float(dt.get('beta', 0.25)),
            rtt_ref_ms=float(dt.get('rtt_ref_ms', 300.0)),
        )
    if baseline == 'B2u':
        ut = algo_cfg.get('utility', {})
        return utility_route(
            q_gate,
            rtt,
            retries,
            K,
            u_threshold=float(ut.get('u_threshold', 0.42)),
            w1=float(ut.get('w1', 1.0)),
            w2=float(ut.get('w2', 0.15)),
            w3=float(ut.get('w3', 0.35)),
            resample_cost=float(ut.get('resample_cost', 1.0)),
            rtt_ref_ms=float(ut.get('rtt_ref_ms', 300.0)),
        )
    return route(q_gate, retries, tau, K)


def fuse_multi_frame_q(
    q_b2: float,
    rng: random.Random,
    lat: LatencyConfig,
    algo_cfg: dict,
) -> Tuple[float, float]:
    """Return (fused_q, extra_iqa_ms)."""
    mf = algo_cfg.get('multi_frame', {})
    n_burst = int(mf.get('burst_frames', 3))
    lam = float(mf.get('ema_lambda', 0.6))
    noise = float(mf.get('noise_std', 0.025))
    scores = simulate_burst_scores(q_b2, n_burst, rng, noise_std=noise)
    extra_ms = (n_burst - 1) * sample_edge_iqa_ms(rng, lat)
    return fuse_burst_scores(scores, lam), extra_ms


def pick_gate(
    baseline: str,
    q_b2: float,
    q_b3: float,
    flags: List[str],
    retries: int,
    tau_b2: float,
    tau_b3: float,
) -> Tuple[float, float, str]:
    if baseline == 'B2':
        return q_b2, tau_b2, 'b2'
    if baseline in ('B2d', 'B2m', 'B2u'):
        return q_b2, tau_b2, baseline.lower()
    if baseline == 'B3':
        return q_b3, tau_b2, 'b3_tau_b2'
    if baseline == 'B3t':
        return q_b3, tau_b3, 'b3_tau_b3'
    if baseline == 'B4':
        q, tau, tier = hybrid_gate(q_b2, q_b3, flags, retries, tau_b2, tau_b3)
        return q, tau, tier
    raise ValueError(f'unsupported baseline for closed-loop: {baseline}')


@trace_call(log_result=False)
def simulate_frame(
    baseline: str,
    plan: dict,
    rng: random.Random,
    cfg: dict,
    lat: LatencyConfig,
    tau_b2: float,
    tau_b3: float,
    K: int,
    physics_cfg: dict,
    use_roi: bool,
    roi_padding: float,
    merged_cfg: dict,
    algo_cfg: dict,
) -> Tuple[float, float, int, str, int, str]:
    entry = plan['entry']
    raw_clear = plan['raw_clear']
    image_bytes = plan['image_bytes']
    meta = {'blur_radius': plan.get('blur_radius'), 'degraded': plan['degraded']}
    skill_used = ''

    q_b2, flags = score_b2(image_bytes, entry, use_roi=use_roi, roi_padding=roi_padding)
    q_b3 = score_b3(image_bytes, entry, merged_cfg)

    rtt = lat.capture_ms
    retries = 0
    final_route = 'fail_safe'
    valid = 0
    q_gate = q_b2

    if baseline == 'B0':
        rtt += sample_cloud_upload_ms(rng, lat)
        if q_b2 < tau_b2:
            rtt += rng.uniform(
                float(cfg.get('b0_bad_upload_penalty_min', 120)),
                float(cfg.get('b0_bad_upload_penalty_max', 220)),
            )
        final_route = 'upload_cloud'
        valid = 1 if q_b2 >= tau_b2 else 0
        return q_b2, rtt, retries, final_route, valid, skill_used

    while True:
        rtt += sample_edge_iqa_ms(rng, lat)

        if baseline == 'B1':
            rtt += lat.route_ms
            rtt += sample_cloud_upload_ms(rng, lat)
            final_route = 'upload_cloud'
            valid = 1 if q_b2 >= tau_b2 else 0
            q_gate = q_b2
            return q_gate, rtt, retries, final_route, valid, skill_used

        q_gate, tau, tier = pick_gate(baseline, q_b2, q_b3, flags, retries, tau_b2, tau_b3)
        if baseline == 'B2m':
            q_gate, extra_iqa = fuse_multi_frame_q(q_gate, rng, lat, algo_cfg)
            rtt += extra_iqa
        rtt += lat.route_ms
        decision = resolve_decision(
            baseline, q_gate, retries, tau, K, rtt, rng, algo_cfg, cfg.get('latency', {})
        )

        if decision == 'upload_cloud':
            rtt += sample_cloud_upload_ms(rng, lat)
            final_route = 'upload_cloud'
            valid = 1
            return q_gate, rtt, retries, final_route, valid, skill_used or tier

        if decision == 'resample_edge':
            retries += 1
            rtt += sample_resample_ms(rng, lat)
            image_bytes, meta, skill_used = apply_resample_transform(
                raw_clear, meta, flags, retries, rng, physics_cfg
            )
            q_b2, flags = score_b2(image_bytes, entry, use_roi=use_roi, roi_padding=roi_padding)
            q_b3 = score_b3(image_bytes, entry, merged_cfg)
            if retries > K:
                final_route = 'fail_safe'
                valid = 0
                q_gate, _, _ = pick_gate(
                    baseline, q_b2, q_b3, flags, retries, tau_b2, tau_b3
                )
                return q_gate, rtt, retries, final_route, valid, skill_used
            continue

        final_route = 'fail_safe'
        valid = 0
        return q_gate, rtt, retries, final_route, valid, skill_used or tier


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


@trace_call(log_result=False)
def run_seed(
    cfg: dict,
    tcm_cfg: dict,
    physics_cfg: dict,
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
    tau_b2 = load_tau_b2()
    tau_b3 = load_tau_b3()
    K = int(cfg['retry_budget_K'])
    rng = random.Random(seed)
    n_frames = int(cfg.get('n_frames_per_baseline', 500))
    n_frames = min(n_frames, len(test_entries))
    bl_list = baselines or cfg['baselines']
    need_b3 = any(b in bl_list for b in ('B3', 'B3t', 'B4'))
    import logging

    log = logging.getLogger('paper1.run_matrix_tcm')
    log.info(
        'run_seed ENTER seed=%s baselines=%s n_frames=%s need_b3=%s',
        seed,
        bl_list,
        n_frames,
        need_b3,
    )
    r_min = float(tcm_cfg.get('blur_radius_min', 2.5))
    r_max = float(tcm_cfg.get('blur_radius_max', 5.0))
    use_roi = bool(tcm_cfg.get('use_roi', True))
    roi_padding = float(tcm_cfg.get('roi_padding', 0.08))
    merged_cfg = {**cfg, **tcm_cfg}
    algo_path = cfg.get('algo_enhance_config')
    algo_cfg = load_algo_cfg(PAPER1_ROOT / algo_path) if algo_path else load_algo_cfg()

    indices = list(range(len(test_entries)))
    rng.shuffle(indices)
    frame_plan = []
    for i in range(n_frames):
        entry = test_entries[indices[i % len(indices)]]
        path = Path(entry['path'])
        raw = path.read_bytes()
        if rng.random() < 0.5:
            image_bytes = raw
            blur_radius = None
            degraded = False
        else:
            blur_radius = rng.uniform(r_min, r_max)
            image_bytes = blur_bytes(raw, blur_radius)
            degraded = True
        q_b2, flags = score_b2(image_bytes, entry, use_roi=use_roi, roi_padding=roi_padding)
        q_b3 = score_b3(image_bytes, entry, merged_cfg) if need_b3 else 0.0
        frame_plan.append(
            {
                'entry': entry,
                'raw_clear': raw,
                'image_bytes': image_bytes,
                'blur_radius': blur_radius,
                'degraded': degraded,
                'flags_init': flags,
                'q_b2_init': q_b2,
                'q_b3_init': q_b3,
            }
        )
        log_progress(log, i + 1, n_frames, every=50, label=f'frame_plan seed={seed}')

    detail_rows: List[dict] = []
    summary_rows: List[dict] = []

    for baseline in bl_list:
        frame_rows = []
        for fid, plan in enumerate(frame_plan):
            q, rtt, retry, rd, valid, skill = simulate_frame(
                baseline,
                plan,
                rng,
                cfg,
                lat,
                tau_b2,
                tau_b3,
                K,
                physics_cfg,
                use_roi,
                roi_padding,
                merged_cfg,
                algo_cfg,
            )
            row = {
                'baseline': baseline,
                'seed': seed,
                'frame_id': fid,
                'q_img': round(q, 4),
                'q_b2_init': round(plan['q_b2_init'], 4),
                'q_b3_init': round(plan['q_b3_init'], 4),
                'degraded': int(plan['degraded']),
                'rtt_ms': round(rtt, 2),
                'retry_count': retry,
                'route_decision': rd,
                'valid': valid,
                'skill_invoked': skill,
            }
            frame_rows.append(row)
            detail_rows.append(row)
            log_progress(
                log,
                fid + 1,
                n_frames,
                every=100,
                label=f'simulate baseline={baseline} seed={seed}',
            )
        summary_rows.append({'baseline': baseline, 'seed': seed, **aggregate_metrics(frame_rows)})
        log.info(
            'run_seed baseline=%s seed=%s metrics=%s',
            baseline,
            seed,
            summary_rows[-1],
        )

    log.info('run_seed EXIT seed=%s n_detail=%s', seed, len(detail_rows))
    return detail_rows, summary_rows


def write_csv(path: Path, rows: List[dict], fieldnames: List[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def main() -> int:
    init_trace(__file__)
    import logging

    log = logging.getLogger('paper1.run_matrix_tcm')
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=str(DEFAULT_CFG))
    parser.add_argument('--tcm-config', type=str, default=str(TCM_CFG))
    parser.add_argument('--physics-config', type=str, default=str(PHYSICS_CFG))
    parser.add_argument('--baseline', type=str, default='')
    parser.add_argument('--seed', type=int, default=-1)
    parser.add_argument('--n-frames', type=int, default=0, help='override n_frames_per_baseline')
    parser.add_argument('--tag', type=str, default='', help='e.g. quick -> table_ii_quick.json')
    args = parser.parse_args()

    cfg = load_yaml(Path(args.config))
    if args.n_frames > 0:
        cfg = {**cfg, 'n_frames_per_baseline': args.n_frames}
    log.info(
        'main config=%s baselines=%s seeds=%s n_frames=%s tag=%s',
        args.config,
        cfg.get('baselines'),
        cfg.get('seeds'),
        cfg.get('n_frames_per_baseline'),
        args.tag or 'full',
    )
    tcm_cfg = load_yaml(Path(args.tcm_config))
    physics_cfg = load_physics_cfg(Path(args.physics_config))
    test_json = PAPER1_ROOT / 'experiments/splits/tcm_test.json'
    if not test_json.is_file():
        raise SystemExit(f'missing {test_json}; run import_shezhenv3.py first')
    test_entries = json.loads(test_json.read_text(encoding='utf-8'))

    seeds = cfg['seeds'] if args.seed < 0 else [args.seed]
    baselines = [args.baseline] if args.baseline else None
    results_dir = PAPER1_ROOT / 'experiments' / 'results'
    all_summary: List[dict] = []

    detail_fields = [
        'baseline',
        'seed',
        'frame_id',
        'q_img',
        'q_b2_init',
        'q_b3_init',
        'degraded',
        'rtt_ms',
        'retry_count',
        'route_decision',
        'valid',
        'skill_invoked',
    ]

    for seed in seeds:
        detail, summary = run_seed(cfg, tcm_cfg, physics_cfg, test_entries, seed, baselines)
        write_csv(results_dir / f'main_seed{seed}_detail.csv', detail, detail_fields)
        write_csv(
            results_dir / f'main_seed{seed}.csv',
            summary,
            ['baseline', 'seed', 'n', 'm1_p50_ms', 'm1_p95_ms', 'm2_valid_rate', 'm3_retry_rate'],
        )
        all_summary.extend(summary)
        print(
            f'seed {seed}: {len(detail)} rows, tau_b2={load_tau_b2()}, tau_b3={load_tau_b3()}'
        )

    tag = args.tag.strip()
    table_name = f'table_ii_{tag}.json' if tag else 'table_ii.json'
    meta_name = f'table_ii_{tag}_meta.json' if tag else 'table_ii_meta.json'
    table_path = results_dir / table_name
    meta = {
        'dataset': 'shezhenv3-coco',
        'split': 'test',
        'n_test_images': len(test_entries),
        'tau_b2': load_tau_b2(),
        'tau_b3': load_tau_b3(),
        'seeds': seeds,
        'use_roi': bool(tcm_cfg.get('use_roi', True)),
        'resample_model': 'physical_skill_transform',
        'baselines': cfg.get('baselines'),
        'n_frames_per_baseline': cfg.get('n_frames_per_baseline'),
        'mode': tag or 'full',
    }
    table_path.write_text(json.dumps(all_summary, indent=2), encoding='utf-8')
    (results_dir / meta_name).write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'Table data -> {table_path} (mode={meta["mode"]})')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
