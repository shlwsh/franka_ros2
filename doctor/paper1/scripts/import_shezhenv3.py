#!/usr/bin/env python3
"""Import ShezhenV3-COCO splits into Paper I experiments/splits/*.json."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

PAPER1_ROOT = Path(__file__).resolve().parents[1]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from paper1_trace import init_trace

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'


def load_cfg(path: Path) -> dict:
    return yaml.safe_load(path.read_text(encoding='utf-8'))


def import_split(root: Path, split: str) -> list[dict]:
    ann_path = root / split / 'annotations' / f'{split}.json'
    if not ann_path.is_file():
        raise FileNotFoundError(ann_path)
    data = json.loads(ann_path.read_text(encoding='utf-8'))
    img_dir = root / split / 'images'

    bbox_map: dict[int, list[list[float]]] = {}
    for ann in data.get('annotations', []):
        image_id = ann.get('image_id')
        bbox = ann.get('bbox')
        if image_id is None or not bbox or len(bbox) < 4:
            continue
        bbox_map.setdefault(int(image_id), []).append([float(v) for v in bbox[:4]])

    entries = []
    for img in data.get('images', []):
        fname = img.get('file_name') or img.get('filename')
        if not fname:
            continue
        rel = f'{split}/images/{fname}'
        abs_path = img_dir / fname
        if not abs_path.is_file():
            continue
        image_id = img.get('id')
        bboxes = bbox_map.get(int(image_id), []) if image_id is not None else []
        entries.append(
            {
                'path': str(abs_path),
                'rel_path': rel,
                'image_id': image_id,
                'width': img.get('width'),
                'height': img.get('height'),
                'bboxes': bboxes,
                'split': split,
                'source': 'shezhenv3-coco',
            }
        )
    return entries


def main() -> int:
    init_trace(__file__)
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=str(DEFAULT_CFG))
    args = parser.parse_args()

    cfg = load_cfg(Path(args.config))
    root = Path(cfg['dataset_root'])
    if not root.is_dir():
        raise SystemExit(f'dataset root not found: {root}')

    out_dir = PAPER1_ROOT / 'experiments' / 'splits'
    out_dir.mkdir(parents=True, exist_ok=True)
    stats = {}
    for split in cfg.get('splits', ['train', 'val', 'test']):
        entries = import_split(root, split)
        out_path = out_dir / f'tcm_{split}.json'
        out_path.write_text(json.dumps(entries, indent=2), encoding='utf-8')
        stats[split] = len(entries)
        print(f'Wrote {len(entries)} entries -> {out_path}')

    meta = {
        'dataset': cfg.get('dataset_name', 'shezhenv3-coco'),
        'root': str(root),
        'counts': stats,
        'total': sum(stats.values()),
    }
    meta_path = out_dir / 'tcm_meta.json'
    meta_path.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'Meta -> {meta_path}: {meta}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
