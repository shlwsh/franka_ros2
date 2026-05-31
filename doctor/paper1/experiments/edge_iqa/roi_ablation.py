#!/usr/bin/env python3
"""Compare Edge-IQA clear/blur separation: full frame vs COCO tongue ROI."""

from __future__ import annotations

import json
import random
import statistics
import sys
from io import BytesIO
from pathlib import Path

import yaml
from PIL import ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[2]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.coco_roi import bbox_from_entry
from edge_iqa.scorer import compute_q_from_bytes
from paper1_trace import init_trace, log_progress, trace_call

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'
OUT_JSON = PAPER1_ROOT / 'experiments/results/roi_ablation.json'


def blur_bytes(data: bytes, radius: float) -> bytes:
    from io import BytesIO
    from PIL import Image

    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def score_cohort(entries: list, *, use_roi: bool, cfg: dict) -> dict:
    import logging

    log = logging.getLogger('paper1.roi_ablation')
    r_min = float(cfg.get('blur_radius_min', 2.5))
    r_max = float(cfg.get('blur_radius_max', 5.0))
    roi_padding = float(cfg.get('roi_padding', 0.08))
    rng = random.Random(42)
    clear_q, blur_q = [], []
    mode = 'tongue_roi' if use_roi else 'full_frame'
    total = len(entries)
    log.info('score_cohort ENTER mode=%s n=%s', mode, total)

    for idx, item in enumerate(entries, start=1):
        path = Path(item['path'])
        if not path.is_file():
            log_progress(log, idx, total, every=50, label=f'score_cohort[{mode}]', extra='skip missing')
            continue
        raw = path.read_bytes()
        bboxes = bbox_from_entry(item)
        kwargs = {
            'bboxes': bboxes,
            'use_roi': use_roi,
            'roi_padding': roi_padding,
        }
        clear_q.append(compute_q_from_bytes(raw, **kwargs).q_img)
        radius = rng.uniform(r_min, r_max)
        blur_q.append(compute_q_from_bytes(blur_bytes(raw, radius), **kwargs).q_img)
        log_progress(log, idx, total, every=50, label=f'score_cohort[{mode}]')

    med_clear = statistics.median(clear_q)
    med_blur = statistics.median(blur_q)
    tau = round((med_clear + med_blur) / 2.0, 3)
    separation = min(clear_q) - max(blur_q)
    result = {
        'use_roi': use_roi,
        'n': len(clear_q),
        'median_clear': round(med_clear, 4),
        'median_blur': round(med_blur, 4),
        'tau': tau,
        'separation_min_clear_max_blur': round(separation, 4),
        'clear_mean': round(statistics.mean(clear_q), 4),
        'blur_mean': round(statistics.mean(blur_q), 4),
    }
    log.info('score_cohort EXIT mode=%s result=%s', mode, result)
    return result


@trace_call()
def main() -> int:
    init_trace(__file__)
    import logging

    log = logging.getLogger('paper1.roi_ablation')
    cfg = yaml.safe_load(DEFAULT_CFG.read_text(encoding='utf-8'))
    val_json = PAPER1_ROOT / 'experiments/splits/tcm_val.json'
    if not val_json.is_file():
        raise SystemExit('run import_shezhenv3.py first')
    entries = json.loads(val_json.read_text(encoding='utf-8'))

    full = score_cohort(entries, use_roi=False, cfg=cfg)
    roi = score_cohort(entries, use_roi=True, cfg=cfg)
    payload = {
        'dataset': cfg.get('dataset_name', 'shezhenv3-coco'),
        'split': 'val',
        'full_frame': full,
        'tongue_roi': roi,
        'delta_separation': round(
            roi['separation_min_clear_max_blur'] - full['separation_min_clear_max_blur'],
            4,
        ),
        'delta_median_gap': round(
            (roi['median_clear'] - roi['median_blur'])
            - (full['median_clear'] - full['median_blur']),
            4,
        ),
    }
    OUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(json.dumps(payload, indent=2), encoding='utf-8')
    log.info('Wrote %s', OUT_JSON)
    print(json.dumps(payload, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
