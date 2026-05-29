#!/usr/bin/env python3
"""Generate synthetic clear/blur val images for phase 2 (no TCM download required)."""

from __future__ import annotations

import json
import random
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter

PAPER1_ROOT = Path(__file__).resolve().parents[1]
OUT_CLEAR = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
OUT_BLUR = PAPER1_ROOT / 'experiments' / 'synthetic' / 'blur'
SPLITS = PAPER1_ROOT / 'experiments' / 'splits'
N_PER_CLASS = 120


def _tongue_like(seed: int, blur: bool) -> Image.Image:
    rng = np.random.default_rng(seed)
    h, w = 512, 512
    y, x = np.mgrid[0:h, 0:w]
    cy, cx = h // 2 + int(rng.integers(-20, 20)), w // 2 + int(rng.integers(-20, 20))
    ry, rx = int(rng.integers(140, 200)), int(rng.integers(100, 160))
    mask = ((x - cx) ** 2 / (rx**2 + 1) + (y - cy) ** 2 / (ry**2 + 1)) <= 1.0
    base = rng.uniform(0.15, 0.25, (h, w))
    tongue = rng.uniform(0.45, 0.75, (h, w))
    arr = np.where(mask, tongue, base)
    arr += rng.normal(0, 0.02, (h, w))
    arr = np.clip(arr, 0, 1)
    rgb = np.stack([arr * 1.05, arr * 0.85, arr * 0.75], axis=-1)
    rgb = (rgb * 255).astype(np.uint8)
    img = Image.fromarray(rgb, mode='RGB')
    if blur:
        img = img.filter(ImageFilter.GaussianBlur(radius=float(rng.uniform(2.5, 5.0))))
    return img


def main() -> None:
    OUT_CLEAR.mkdir(parents=True, exist_ok=True)
    OUT_BLUR.mkdir(parents=True, exist_ok=True)
    SPLITS.mkdir(parents=True, exist_ok=True)

    val_entries = []
    for i in range(N_PER_CLASS):
        clear_path = OUT_CLEAR / f'clear_{i:04d}.png'
        blur_path = OUT_BLUR / f'blur_{i:04d}.png'
        _tongue_like(i, blur=False).save(clear_path)
        _tongue_like(i + 10_000, blur=True).save(blur_path)
        val_entries.append({'path': str(clear_path.relative_to(PAPER1_ROOT)), 'label': 'clear'})
        val_entries.append({'path': str(blur_path.relative_to(PAPER1_ROOT)), 'label': 'blur'})

    random.shuffle(val_entries)
    (SPLITS / 'val.json').write_text(json.dumps(val_entries, indent=2), encoding='utf-8')
    print(f'Wrote {len(val_entries)} val entries -> {SPLITS / "val.json"}')


if __name__ == '__main__':
    main()
