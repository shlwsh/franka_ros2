"""Tests for physical resample transforms."""

from __future__ import annotations

import random
import sys
from io import BytesIO
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.scorer import compute_q_from_bytes
from sim.resample_physics import apply_resample_transform, load_physics_cfg


def _solid_image(val: float = 0.3) -> bytes:
    arr = np.full((128, 128, 3), int(val * 255), dtype=np.uint8)
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format='PNG')
    return buf.getvalue()


def _blur(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def _textured_image() -> bytes:
    arr = np.zeros((128, 128, 3), dtype=np.uint8)
    arr[::4, ::4] = 200
    arr[2::4, 2::4] = 80
    buf = BytesIO()
    Image.fromarray(arr).save(buf, format='PNG')
    return buf.getvalue()


def test_blur_resample_increases_q():
    cfg = load_physics_cfg()
    raw = _textured_image()
    heavy = _blur(raw, 4.5)
    q_heavy = compute_q_from_bytes(heavy).q_img
    meta = {'blur_radius': 4.5, 'degraded': True}
    rng = random.Random(0)
    out, new_meta, skill = apply_resample_transform(
        raw, meta, ['blur'], 1, rng, cfg
    )
    q_after = compute_q_from_bytes(out).q_img
    assert skill == 'adaptive_visual_damping'
    assert new_meta['blur_radius'] < 4.5
    assert q_after > q_heavy


def test_exposure_resample_underexposed():
    cfg = load_physics_cfg()
    raw = _solid_image(0.12)
    meta = {'blur_radius': None, 'degraded': False}
    rng = random.Random(1)
    out, _, skill = apply_resample_transform(
        raw, meta, ['underexposed'], 1, rng, cfg
    )
    assert skill == 'exposure_loop_tuning'
    q_before = compute_q_from_bytes(raw).q_img
    q_after = compute_q_from_bytes(out).q_img
    assert q_after >= q_before


def test_hybrid_gate_tiers():
    from langgraph_router.hybrid_route import hybrid_gate

    q, tau, tier = hybrid_gate(0.5, 0.9, ['underexposed'], 1, 0.465, 0.6)
    assert tier == 'tier_a_exposure' and tau == 0.465
    q, tau, tier = hybrid_gate(0.5, 0.9, [], 0, 0.465, 0.6)
    assert tier == 'tier_a_first'
    q, tau, tier = hybrid_gate(0.5, 0.9, ['blur'], 1, 0.465, 0.6)
    assert tier == 'tier_b_blur' and tau == 0.6
