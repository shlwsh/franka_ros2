"""Physical skill response transforms for offline resample replay (Paper I)."""

from __future__ import annotations

import random
from io import BytesIO
from pathlib import Path
from typing import Any

import numpy as np
import yaml
from PIL import Image, ImageFilter

DEFAULT_CFG = (
    Path(__file__).resolve().parents[1] / 'experiments/configs/resample_physics.yaml'
)

EXPOSURE_FLAGS = ('underexposed', 'overexposed', 'poor_exposure')


def load_physics_cfg(path: Path | None = None) -> dict:
    cfg_path = path or DEFAULT_CFG
    return yaml.safe_load(cfg_path.read_text(encoding='utf-8'))


def gaussian_blur_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def apply_exposure_bytes(data: bytes, gain: float, bias: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        arr = np.asarray(im.convert('RGB'), dtype=np.float32) / 255.0
        arr = np.clip(arr * gain + bias, 0.0, 1.0)
        out = Image.fromarray((arr * 255.0).astype(np.uint8))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def pick_exposure_flag(flags: list[str], cfg: dict) -> str | None:
    priority = cfg.get('exposure_flag_priority', list(EXPOSURE_FLAGS))
    flag_set = set(flags)
    for name in priority:
        if name in flag_set:
            return name
    return None


def apply_resample_transform(
    raw_clear: bytes,
    meta: dict[str, Any],
    flags: list[str],
    retry_idx: int,
    rng: random.Random,
    physics_cfg: dict,
) -> tuple[bytes, dict[str, Any], str]:
    """
    Apply skill-equivalent transform after resample_edge.

    Returns (new_image_bytes, updated_meta, skill_name).
    """
    blur_cfg = physics_cfg.get('blur', {})
    alpha_range = blur_cfg.get('alpha_range', [0.4, 0.6])
    r_min = float(blur_cfg.get('r_min', 1.0))
    default_r = float(blur_cfg.get('default_blur_radius', 3.0))

    exposure_flag = pick_exposure_flag(flags, physics_cfg)
    if exposure_flag:
        params = physics_cfg.get('exposure', {}).get(exposure_flag, {})
        gain = float(params.get('gain', 1.0))
        bias = float(params.get('bias', 0.0))
        skill = physics_cfg.get('exposure', {}).get('skill_name', 'exposure_loop_tuning')
        out = apply_exposure_bytes(raw_clear, gain, bias)
        new_meta = {**meta, 'blur_radius': None, 'degraded': False, 'last_skill': skill}
        return out, new_meta, skill

    skill = blur_cfg.get('skill_name', 'adaptive_visual_damping')
    blur_radius = meta.get('blur_radius')
    if blur_radius is None:
        blur_radius = default_r
    alpha = rng.uniform(float(alpha_range[0]), float(alpha_range[1]))
    new_r = max(r_min, float(blur_radius) * alpha)
    if retry_idx >= 2:
        new_r = max(r_min, new_r * alpha)
    out = gaussian_blur_bytes(raw_clear, new_r)
    new_meta = {
        **meta,
        'blur_radius': new_r,
        'degraded': new_r > r_min + 0.05,
        'last_skill': skill,
    }
    return out, new_meta, skill
