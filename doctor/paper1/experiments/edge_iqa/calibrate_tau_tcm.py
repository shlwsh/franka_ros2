#!/usr/bin/env python3
"""Build clear/blur calibration cohort from ShezhenV3 val split."""

from __future__ import annotations

import argparse
import csv
import json
import random
import sys
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image, ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[2]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.scorer import compute_q_from_bytes

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'
OUT_CSV = PAPER1_ROOT / 'experiments/results/calibration_val.csv'
OUT_TAU = PAPER1_ROOT / 'experiments/results/recommended_tau.json'
OUT_STATS = PAPER1_ROOT / 'experiments/results/tcm_calibration_stats.json'


def load_cfg(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def blur_image_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        blurred = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        blurred.save(buf, format='PNG')
        return buf.getvalue()


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=str(DEFAULT_CFG))
    parser.add_argument('--max-val', type=int, default=0, help='0 = all val images')
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()

    cfg = load_cfg(Path(args.config))
    val_json = PAPER1_ROOT / 'experiments/splits/tcm_val.json'
    if not val_json.is_file():
        raise SystemExit(f'missing {val_json}; run scripts/import_shezhenv3.py first')

    entries = json.loads(val_json.read_text(encoding='utf-8'))
    if args.max_val > 0:
        rng = random.Random(args.seed)
        entries = rng.sample(entries, min(args.max_val, len(entries)))

    r_min = float(cfg.get('blur_radius_min', 2.5))
    r_max = float(cfg.get('blur_radius_max', 5.0))
    rng = random.Random(args.seed)

    rows = []
    clear_q, blur_q = [], []

    for item in entries:
        path = Path(item['path'])
        if not path.is_file():
            continue
        raw = path.read_bytes()
        r_clear = compute_q_from_bytes(raw)
        rows.append(
            {
                'path': item.get('rel_path', str(path)),
                'label': 'clear',
                'q_img': r_clear.q_img,
                'flags': ';'.join(r_clear.flags),
                'source': 'shezhenv3-coco',
            }
        )
        clear_q.append(r_clear.q_img)

        radius = rng.uniform(r_min, r_max)
        blurred = blur_image_bytes(raw, radius)
        r_blur = compute_q_from_bytes(blurred)
        rows.append(
            {
                'path': f'{item.get("rel_path", path.name)}#blur_r{radius:.2f}',
                'label': 'blur',
                'q_img': r_blur.q_img,
                'flags': ';'.join(r_blur.flags),
                'source': 'shezhenv3-coco',
            }
        )
        blur_q.append(r_blur.q_img)

    if not clear_q or not blur_q:
        raise SystemExit('no valid val images scored')

    import statistics

    med_clear = statistics.median(clear_q)
    med_blur = statistics.median(blur_q)
    tau = round((med_clear + med_blur) / 2.0, 3)
    tau = max(0.45, min(0.65, tau))
    separation = min(clear_q) - max(blur_q)

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'label', 'q_img', 'flags', 'source'])
        writer.writeheader()
        writer.writerows(rows)

    tau_payload = {
        'tau': tau,
        'median_clear': med_clear,
        'median_blur': med_blur,
        'n_val': len(rows),
        'n_clear': len(clear_q),
        'n_blur': len(blur_q),
        'separation_min_clear_max_blur': round(separation, 4),
        'dataset': 'shezhenv3-coco',
    }
    OUT_TAU.write_text(json.dumps(tau_payload, indent=2), encoding='utf-8')

    stats = {
        **tau_payload,
        'clear_mean': round(statistics.mean(clear_q), 4),
        'blur_mean': round(statistics.mean(blur_q), 4),
        'clear_std': round(statistics.pstdev(clear_q), 4),
        'blur_std': round(statistics.pstdev(blur_q), 4),
    }
    OUT_STATS.write_text(json.dumps(stats, indent=2), encoding='utf-8')
    print(json.dumps(stats, indent=2))
    print(f'Wrote {OUT_CSV} ({len(rows)} rows), tau={tau} -> {OUT_TAU}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
