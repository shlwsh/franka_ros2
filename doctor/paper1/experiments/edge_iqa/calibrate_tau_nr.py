#!/usr/bin/env python3
"""Calibrate tau and q-mapping for Bbrisque / Bniqe on ShezhenV3 val split."""

from __future__ import annotations

import argparse
import json
import random
import statistics
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
import yaml
from PIL import Image, ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.coco_roi import bbox_from_entry
from edge_iqa.nr_iqa import (
    _mscn_coefficients,
    brisque_raw_from_bytes,
    raw_to_q,
)

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'


def blur_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def build_niqe_reference(entries: list, cfg: dict, seed: int) -> dict:
    rng = random.Random(seed)
    r_min = float(cfg.get('blur_radius_min', 2.5))
    r_max = float(cfg.get('blur_radius_max', 5.0))
    use_roi = bool(cfg.get('use_roi', True))
    roi_padding = float(cfg.get('roi_padding', 0.08))
    feats = []
    for item in entries:
        path = Path(item['path'])
        if not path.is_file():
            continue
        bboxes = bbox_from_entry(item)
        raw = path.read_bytes()
        from PIL import Image

        with Image.open(BytesIO(raw)) as im:
            rgb = im.convert('RGB')
            if use_roi and bboxes:
                from edge_iqa.coco_roi import crop_roi

                rgb = crop_roi(rgb, bboxes, padding=roi_padding)
            rgb = rgb.resize((512, 512), Image.Resampling.BILINEAR)
            gray = (
                0.299 * np.asarray(rgb)[:, :, 0]
                + 0.587 * np.asarray(rgb)[:, :, 1]
                + 0.114 * np.asarray(rgb)[:, :, 2]
            ).astype(np.float64) / 255.0
        feats.append(_mscn_coefficients(gray))
    mat = np.stack(feats, axis=0)
    mean = mat.mean(axis=0)
    cov = np.cov(mat.T) + np.eye(mat.shape[1]) * 1e-6
    cov_inv = np.linalg.inv(cov)
    ref_path = PAPER1_ROOT / 'experiments/results/niqe_nss_ref.json'
    ref_path.write_text(
        json.dumps({'mean': mean.tolist(), 'cov_inv': cov_inv.tolist()}, indent=2),
        encoding='utf-8',
    )
    return {'mean': mean.tolist(), 'cov_inv': cov_inv.tolist()}


def calibrate_method(method: str, entries: list, cfg: dict, seed: int, niqe_ref: dict | None) -> dict:
    rng = random.Random(seed)
    r_min = float(cfg.get('blur_radius_min', 2.5))
    r_max = float(cfg.get('blur_radius_max', 5.0))
    use_roi = bool(cfg.get('use_roi', True))
    roi_padding = float(cfg.get('roi_padding', 0.08))
    clear_raw, blur_raw = [], []

    from edge_iqa.nr_iqa import niqe_nss_raw_from_bytes

    ref_mean = np.array(niqe_ref['mean']) if niqe_ref else None
    ref_cov_inv = np.array(niqe_ref['cov_inv']) if niqe_ref else None

    for item in entries:
        path = Path(item['path'])
        if not path.is_file():
            continue
        bboxes = bbox_from_entry(item)
        raw_b = path.read_bytes()
        kwargs = {'bboxes': bboxes, 'use_roi': use_roi, 'roi_padding': roi_padding}
        if method == 'Bbrisque':
            clear_raw.append(brisque_raw_from_bytes(raw_b, **kwargs))
            blur_raw.append(
                brisque_raw_from_bytes(
                    blur_bytes(raw_b, rng.uniform(r_min, r_max)), **kwargs
                )
            )
        else:
            clear_raw.append(
                niqe_nss_raw_from_bytes(
                    raw_b,
                    ref_mean=ref_mean,
                    ref_cov_inv=ref_cov_inv,
                    **kwargs,
                )
            )
            blur_raw.append(
                niqe_nss_raw_from_bytes(
                    blur_bytes(raw_b, rng.uniform(r_min, r_max)),
                    ref_mean=ref_mean,
                    ref_cov_inv=ref_cov_inv,
                    **kwargs,
                )
            )

    mc, mb = statistics.median(clear_raw), statistics.median(blur_raw)
    clear_q = [raw_to_q(x, raw_clear_median=mc, raw_blur_median=mb) for x in clear_raw]
    blur_q = [raw_to_q(x, raw_clear_median=mc, raw_blur_median=mb) for x in blur_raw]
    tau = (statistics.median(clear_q) + statistics.median(blur_q)) / 2.0
    sep = min(clear_q) - max(blur_q)
    out = {
        'method': method,
        'tau': round(tau, 4),
        'raw_clear_median': mc,
        'raw_blur_median': mb,
        'median_clear_q': statistics.median(clear_q),
        'median_blur_q': statistics.median(blur_q),
        'separation_min_clear_max_blur': round(sep, 4),
        'n_clear': len(clear_q),
        'n_blur': len(blur_q),
        'dataset': 'shezhenv3-coco',
        'use_roi': use_roi,
    }
    fname = 'recommended_tau_brisque.json' if method == 'Bbrisque' else 'recommended_tau_niqe.json'
    (PAPER1_ROOT / 'experiments/results' / fname).write_text(
        json.dumps(out, indent=2), encoding='utf-8'
    )
    print('Wrote', fname, out)
    return out


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', default=str(DEFAULT_CFG))
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding='utf-8'))
    val_json = PAPER1_ROOT / 'experiments/splits/tcm_val.json'
    entries = json.loads(val_json.read_text(encoding='utf-8'))
    niqe_ref = build_niqe_reference(entries, cfg, args.seed)
    calibrate_method('Bbrisque', entries, cfg, args.seed, niqe_ref)
    calibrate_method('Bniqe', entries, cfg, args.seed, niqe_ref)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
