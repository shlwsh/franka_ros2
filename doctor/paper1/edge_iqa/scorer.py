"""Edge-IQA: Laplacian sharpness + exposure fusion (Paper I, V19)."""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
from PIL import Image

from edge_iqa.coco_roi import crop_roi

DEFAULT_SIZE = 512
SHARPNESS_WEIGHT = 0.65
EXPOSURE_WEIGHT = 0.35
BLUR_THRESHOLD = 0.35
UNDEREXPOSED_THRESHOLD = 0.25
OVEREXPOSED_THRESHOLD = 0.85


@dataclass
class ScorerResult:
    q_img: float
    flags: List[str]
    t_iqa_ms: float
    sharpness: float
    exposure: float

    def to_dict(self) -> dict:
        return {
            'q_img': round(self.q_img, 4),
            'flags': self.flags,
            't_iqa_ms': round(self.t_iqa_ms, 3),
            'sharpness': round(self.sharpness, 4),
            'exposure': round(self.exposure, 4),
        }


def _prepare_image(
    image: Image.Image,
    *,
    bboxes: Sequence[Sequence[float]] | None = None,
    roi_padding: float = 0.08,
    use_roi: bool = True,
) -> Image.Image:
    im = image.convert('RGB')
    if use_roi and bboxes:
        im = crop_roi(im, bboxes, padding=roi_padding)
    return im


def _to_gray_array(image: Image.Image, size: int) -> np.ndarray:
    img = image.resize((size, size), Image.Resampling.BILINEAR)
    arr = np.asarray(img, dtype=np.float32) / 255.0
    gray = 0.299 * arr[:, :, 0] + 0.587 * arr[:, :, 1] + 0.114 * arr[:, :, 2]
    return gray


def sharpness_score(gray: np.ndarray) -> float:
    """Laplacian variance mapped to [0, 1] (vectorized, CPU-friendly)."""
    lap = (
        -4.0 * gray
        + np.roll(gray, 1, axis=0)
        + np.roll(gray, -1, axis=0)
        + np.roll(gray, 1, axis=1)
        + np.roll(gray, -1, axis=1)
    )
    variance = float(np.var(lap))
    # Empirical scaling for 512px tongue-like images
    normalized = variance / (variance + 0.002)
    return float(np.clip(normalized, 0.0, 1.0))


def exposure_score(gray: np.ndarray) -> float:
    """Peak at mid-gray; penalize under/over exposure."""
    mean_val = float(np.mean(gray))
    # Triangular preference around 0.45--0.55
    ideal = 0.5
    deviation = abs(mean_val - ideal)
    score = 1.0 - min(deviation / 0.5, 1.0)
    return float(np.clip(score, 0.0, 1.0))


def derive_flags(sharpness: float, exposure: float, gray: np.ndarray) -> List[str]:
    flags: List[str] = []
    if sharpness < BLUR_THRESHOLD:
        flags.append('blur')
    mean_val = float(np.mean(gray))
    if mean_val < UNDEREXPOSED_THRESHOLD:
        flags.append('underexposed')
    elif mean_val > OVEREXPOSED_THRESHOLD:
        flags.append('overexposed')
    elif exposure < 0.4:
        flags.append('poor_exposure')
    return flags


def compute_q(
    image_path: str | Path,
    *,
    resize: int = DEFAULT_SIZE,
    bboxes: Sequence[Sequence[float]] | None = None,
    roi_padding: float = 0.08,
    use_roi: bool = False,
) -> ScorerResult:
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError(f'image not found: {path}')

    t0 = time.perf_counter()
    with Image.open(path) as im:
        prepared = _prepare_image(
            im, bboxes=bboxes, roi_padding=roi_padding, use_roi=use_roi
        )
        gray = _to_gray_array(prepared, resize)

    sharp = sharpness_score(gray)
    expo = exposure_score(gray)
    q = SHARPNESS_WEIGHT * sharp + EXPOSURE_WEIGHT * expo
    flags = derive_flags(sharp, expo, gray)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0

    return ScorerResult(
        q_img=float(np.clip(q, 0.0, 1.0)),
        flags=flags,
        t_iqa_ms=elapsed_ms,
        sharpness=sharp,
        exposure=expo,
    )


def compute_q_from_bytes(
    data: bytes,
    *,
    resize: int = DEFAULT_SIZE,
    bboxes: Sequence[Sequence[float]] | None = None,
    roi_padding: float = 0.08,
    use_roi: bool = False,
) -> ScorerResult:
    import io

    t0 = time.perf_counter()
    with Image.open(io.BytesIO(data)) as im:
        prepared = _prepare_image(
            im, bboxes=bboxes, roi_padding=roi_padding, use_roi=use_roi
        )
        gray = _to_gray_array(prepared, resize)
    sharp = sharpness_score(gray)
    expo = exposure_score(gray)
    q = SHARPNESS_WEIGHT * sharp + EXPOSURE_WEIGHT * expo
    flags = derive_flags(sharp, expo, gray)
    elapsed_ms = (time.perf_counter() - t0) * 1000.0
    return ScorerResult(
        q_img=float(np.clip(q, 0.0, 1.0)),
        flags=flags,
        t_iqa_ms=elapsed_ms,
        sharpness=sharp,
        exposure=expo,
    )
