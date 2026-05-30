"""COCO tongue bounding-box ROI crop for Edge-IQA (Paper I)."""

from __future__ import annotations

from typing import Iterable, List, Sequence, Tuple

from PIL import Image

BBox = Tuple[float, float, float, float]


def union_bbox(bboxes: Sequence[Sequence[float]]) -> BBox | None:
    """Merge COCO boxes [x, y, w, h] into one axis-aligned ROI."""
    if not bboxes:
        return None
    xs, ys, xe, ye = [], [], [], []
    for box in bboxes:
        if len(box) < 4:
            continue
        x, y, w, h = float(box[0]), float(box[1]), float(box[2]), float(box[3])
        if w <= 0 or h <= 0:
            continue
        xs.append(x)
        ys.append(y)
        xe.append(x + w)
        ye.append(y + h)
    if not xs:
        return None
    return (min(xs), min(ys), max(xe) - min(xs), max(ye) - min(ys))


def expand_bbox(bbox: BBox, width: int, height: int, padding: float) -> BBox:
    """Expand ROI by fractional padding on each side, clamped to image bounds."""
    x, y, w, h = bbox
    pad_x = w * padding
    pad_y = h * padding
    x0 = max(0.0, x - pad_x)
    y0 = max(0.0, y - pad_y)
    x1 = min(float(width), x + w + pad_x)
    y1 = min(float(height), y + h + pad_y)
    return (x0, y0, max(1.0, x1 - x0), max(1.0, y1 - y0))


def crop_roi(
    image: Image.Image,
    bboxes: Sequence[Sequence[float]] | None,
    *,
    padding: float = 0.08,
) -> Image.Image:
    """Crop tongue ROI from COCO boxes; return original image if no valid box."""
    if not bboxes:
        return image
    merged = union_bbox(bboxes)
    if merged is None:
        return image
    x, y, w, h = expand_bbox(merged, image.width, image.height, padding)
    left = int(round(x))
    top = int(round(y))
    right = int(round(x + w))
    bottom = int(round(y + h))
    right = min(right, image.width)
    bottom = min(bottom, image.height)
    if right <= left or bottom <= top:
        return image
    return image.crop((left, top, right, bottom))


def bbox_from_entry(entry: dict) -> List[List[float]] | None:
    """Read bbox list from split JSON entry."""
    raw = entry.get('bboxes') or entry.get('bbox')
    if raw is None:
        return None
    if isinstance(raw, list) and raw and isinstance(raw[0], (int, float)):
        return [list(raw)]
    if isinstance(raw, list):
        return [list(b) for b in raw if isinstance(b, (list, tuple)) and len(b) >= 4]
    return None
