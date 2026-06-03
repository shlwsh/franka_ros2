"""No-reference IQA scorers for Paper I appendix baselines (BRISQUE + NSS/NIQE-style)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import List, Sequence

import numpy as np
from PIL import Image

from edge_iqa.coco_roi import crop_roi

MODEL_DIR = Path(__file__).resolve().parent / 'models'
BRISQUE_MODEL = MODEL_DIR / 'brisque_model_live.yml'
BRISQUE_RANGE = MODEL_DIR / 'brisque_range_live.yml'

# Extra edge latency (ms) vs Edge-IQA ~9 ms (Table iqa-compare)
NR_LATENCY_MS = {'Bbrisque': 85.0, 'Bniqe': 150.0}


@dataclass
class NrScore:
    q_img: float
    raw: float
    t_ms: float
    method: str


def _prepare_rgb(
    image: Image.Image,
    *,
    bboxes: Sequence[Sequence[float]] | None,
    use_roi: bool,
    roi_padding: float,
    size: int = 384,
) -> np.ndarray:
    im = image.convert('RGB')
    if use_roi and bboxes:
        im = crop_roi(im, bboxes, padding=roi_padding)
    im = im.resize((size, size), Image.Resampling.BILINEAR)
    return np.asarray(im, dtype=np.uint8)


def _score_brisque_cv2(rgb: np.ndarray) -> float:
    import cv2

    if not BRISQUE_MODEL.is_file() or not BRISQUE_RANGE.is_file():
        raise FileNotFoundError(f'BRISQUE models missing under {MODEL_DIR}')
    assessor = cv2.quality.QualityBRISQUE_create(
        str(BRISQUE_MODEL),
        str(BRISQUE_RANGE),
    )
    return float(assessor.compute(rgb)[0])


def _mscn_coefficients(gray: np.ndarray, block: int = 7) -> np.ndarray:
    """Mean-subtracted contrast-normalized coefficients (NIQE-style blocks)."""
    h, w = gray.shape
    coeffs = []
    for y in range(0, h - block + 1, block):
        for x in range(0, w - block + 1, block):
            patch = gray[y : y + block, x : x + block].astype(np.float64)
            mu = patch.mean()
            sigma = patch.std() + 1e-6
            coeffs.append((patch - mu) / sigma)
    if not coeffs:
        return np.zeros(4, dtype=np.float64)
    stacked = np.concatenate([c.ravel() for c in coeffs])
    return np.array(
        [
            stacked.mean(),
            stacked.std(),
            float(np.mean((stacked - stacked.mean()) ** 3)),
            float(np.mean((stacked - stacked.mean()) ** 4)),
        ],
        dtype=np.float64,
    )


def _score_niqe_nss(gray: np.ndarray, ref_mean: np.ndarray, ref_cov_inv: np.ndarray) -> float:
    feat = _mscn_coefficients(gray)
    delta = feat - ref_mean
    d2 = float(delta @ ref_cov_inv @ delta)
    return d2


def load_niqe_reference(stats_path: Path | None = None) -> tuple[np.ndarray, np.ndarray]:
    """Load or build MVG reference from calibration JSON."""
    path = stats_path or (
        Path(__file__).resolve().parents[1] / 'experiments/results/niqe_nss_ref.json'
    )
    if path.is_file():
        import json

        data = json.loads(path.read_text(encoding='utf-8'))
        return np.array(data['mean'], dtype=np.float64), np.array(
            data['cov_inv'], dtype=np.float64
        )
    raise FileNotFoundError(f'NIQE NSS reference missing: {path}')


def brisque_raw_from_bytes(
    data: bytes,
    *,
    bboxes: Sequence[Sequence[float]] | None = None,
    use_roi: bool = True,
    roi_padding: float = 0.08,
) -> float:
    with Image.open(BytesIO(data)) as im:
        rgb = _prepare_rgb(im, bboxes=bboxes, use_roi=use_roi, roi_padding=roi_padding)
    return _score_brisque_cv2(rgb)


def niqe_nss_raw_from_bytes(
    data: bytes,
    *,
    bboxes: Sequence[Sequence[float]] | None = None,
    use_roi: bool = True,
    roi_padding: float = 0.08,
    ref_mean: np.ndarray | None = None,
    ref_cov_inv: np.ndarray | None = None,
) -> float:
    if ref_mean is None or ref_cov_inv is None:
        ref_mean, ref_cov_inv = load_niqe_reference()
    with Image.open(BytesIO(data)) as im:
        rgb = _prepare_rgb(im, bboxes=bboxes, use_roi=use_roi, roi_padding=roi_padding)
    gray = (
        0.299 * rgb[:, :, 0] + 0.587 * rgb[:, :, 1] + 0.114 * rgb[:, :, 2]
    ).astype(np.float64) / 255.0
    return _score_niqe_nss(gray, ref_mean, ref_cov_inv)


def raw_to_q(raw: float, *, raw_clear_median: float, raw_blur_median: float) -> float:
    """Map raw NR score to [0,1] using validation cohort medians (higher = better)."""
    # Orient so blur cohort maps lower Q than clear cohort after calibration.
    lo = min(raw_clear_median, raw_blur_median)
    hi = max(raw_clear_median, raw_blur_median)
    if hi <= lo + 1e-9:
        return 0.5
    # If blur median > clear median, higher raw = worse (BRISQUE, NSS distance).
    if raw_blur_median > raw_clear_median:
        q = 1.0 - (raw - lo) / (hi - lo)
    else:
        q = (raw - lo) / (hi - lo)
    return float(np.clip(q, 0.0, 1.0))


def score_nr(
    data: bytes,
    method: str,
    *,
    bboxes: Sequence[Sequence[float]] | None = None,
    use_roi: bool = True,
    roi_padding: float = 0.08,
    calib: dict | None = None,
) -> NrScore:
    t0 = time.perf_counter()
    calib = calib or {}
    if method == 'Bbrisque':
        raw = brisque_raw_from_bytes(
            data, bboxes=bboxes, use_roi=use_roi, roi_padding=roi_padding
        )
    elif method == 'Bniqe':
        nm = calib.get('niqe_mean')
        nc = calib.get('niqe_cov_inv')
        ref_mean = np.array(nm, dtype=np.float64) if nm else None
        ref_cov_inv = np.array(nc, dtype=np.float64) if nc else None
        raw = niqe_nss_raw_from_bytes(
            data,
            bboxes=bboxes,
            use_roi=use_roi,
            roi_padding=roi_padding,
            ref_mean=ref_mean,
            ref_cov_inv=ref_cov_inv,
        )
    else:
        raise ValueError(method)
    q = raw_to_q(
        raw,
        raw_clear_median=float(calib['raw_clear_median']),
        raw_blur_median=float(calib['raw_blur_median']),
    )
    t_ms = (time.perf_counter() - t0) * 1000.0
    return NrScore(q_img=q, raw=raw, t_ms=t_ms, method=method)
