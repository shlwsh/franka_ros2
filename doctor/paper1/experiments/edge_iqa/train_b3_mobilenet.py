#!/usr/bin/env python3
"""Train B3 learned IQA (MobileNetV3-Small) on ShezhenV3 train split."""

from __future__ import annotations

import argparse
import json
import random
import sys
from io import BytesIO
from pathlib import Path

import yaml
from PIL import Image, ImageFile, ImageFilter
from torch.utils.data import DataLoader, Dataset

PAPER1_ROOT = Path(__file__).resolve().parents[2]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.coco_roi import bbox_from_entry, crop_roi

ImageFile.LOAD_TRUNCATED_IMAGES = True

DEFAULT_CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'
DEFAULT_OUT = PAPER1_ROOT / 'experiments/results/b3_mobilenet.pt'
DEFAULT_META = PAPER1_ROOT / 'experiments/results/b3_training_meta.json'


class TongueIQADataset(Dataset):
    def __init__(
        self,
        entries: list,
        *,
        roi_padding: float,
        blur_radius_range: tuple[float, float],
        rng: random.Random,
        transform,
        samples_per_image: int = 2,
    ):
        self.entries = entries
        self.roi_padding = roi_padding
        self.blur_range = blur_radius_range
        self.rng = rng
        self.transform = transform
        self.samples_per_image = samples_per_image
        self.index = []
        for i, _ in enumerate(entries):
            for k in range(samples_per_image):
                label = 1 if k == 0 else 0
                self.index.append((i, label))

    def __len__(self) -> int:
        return len(self.index)

    def _load_roi(self, entry: dict) -> Image.Image | None:
        path = Path(entry['path'])
        try:
            with Image.open(path) as im:
                bboxes = bbox_from_entry(entry)
                return crop_roi(im.convert('RGB'), bboxes or [], padding=self.roi_padding)
        except OSError:
            return None

    def __getitem__(self, idx: int):
        import torch

        for _ in range(5):
            entry_idx, label = self.index[idx]
            entry = self.entries[entry_idx]
            image = self._load_roi(entry)
            if image is not None:
                break
            idx = self.rng.randrange(len(self.index))
        else:
            image = Image.new('RGB', (224, 224), color=(128, 128, 128))
        if label == 0:
            radius = self.rng.uniform(*self.blur_range)
            image = image.filter(ImageFilter.GaussianBlur(radius=radius))
        tensor = self.transform(image)
        return tensor, torch.tensor(label, dtype=torch.long)


def blur_image_bytes(data: bytes, radius: float) -> bytes:
    with Image.open(BytesIO(data)) as im:
        out = im.convert('RGB').filter(ImageFilter.GaussianBlur(radius=radius))
        buf = BytesIO()
        out.save(buf, format='PNG')
        return buf.getvalue()


def evaluate_val(model, loader, device) -> float:
    import torch

    model.eval()
    correct = total = 0
    with torch.no_grad():
        for x, y in loader:
            x = x.to(device)
            y = y.to(device)
            pred = model(x).argmax(dim=1)
            correct += int((pred == y).sum().item())
            total += y.size(0)
    return correct / max(total, 1)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument('--config', type=str, default=str(DEFAULT_CFG))
    parser.add_argument('--epochs', type=int, default=8)
    parser.add_argument('--batch-size', type=int, default=32)
    parser.add_argument('--lr', type=float, default=1e-3)
    parser.add_argument('--input-size', type=int, default=224)
    parser.add_argument('--max-train', type=int, default=0, help='0 = all train')
    parser.add_argument('--seed', type=int, default=42)
    parser.add_argument('--out', type=str, default=str(DEFAULT_OUT))
    args = parser.parse_args()

    import torch
    import torch.nn as nn
    from torchvision import models, transforms

    cfg = yaml.safe_load(Path(args.config).read_text(encoding='utf-8'))
    roi_padding = float(cfg.get('roi_padding', 0.08))
    blur_range = (
        float(cfg.get('blur_radius_min', 2.5)),
        float(cfg.get('blur_radius_max', 5.0)),
    )

    train_json = PAPER1_ROOT / 'experiments/splits/tcm_train.json'
    val_json = PAPER1_ROOT / 'experiments/splits/tcm_val.json'
    if not train_json.is_file() or not val_json.is_file():
        raise SystemExit('run import_shezhenv3.py first')

    train_entries = json.loads(train_json.read_text(encoding='utf-8'))
    val_entries = json.loads(val_json.read_text(encoding='utf-8'))
    rng = random.Random(args.seed)

    def filter_valid(entries: list) -> list:
        valid = []
        for item in entries:
            path = Path(item['path'])
            if not path.is_file():
                continue
            try:
                with Image.open(path) as im:
                    im.verify()
                valid.append(item)
            except OSError:
                continue
        return valid

    train_entries = filter_valid(train_entries)
    val_entries = filter_valid(val_entries)
    if args.max_train > 0:
        train_entries = rng.sample(train_entries, min(args.max_train, len(train_entries)))

    print(
        f'train_images={len(train_entries)} val_images={len(val_entries)} device-pending',
        flush=True,
    )

    transform = transforms.Compose(
        [
            transforms.Resize((args.input_size, args.input_size)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.ColorJitter(brightness=0.1, contrast=0.1),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    val_transform = transforms.Compose(
        [
            transforms.Resize((args.input_size, args.input_size)),
            transforms.ToTensor(),
            transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )

    train_ds = TongueIQADataset(
        train_entries,
        roi_padding=roi_padding,
        blur_radius_range=blur_range,
        rng=random.Random(args.seed + 1),
        transform=transform,
    )
    val_ds = TongueIQADataset(
        val_entries,
        roi_padding=roi_padding,
        blur_radius_range=blur_range,
        rng=random.Random(args.seed + 2),
        transform=val_transform,
        samples_per_image=2,
    )

    train_loader = DataLoader(train_ds, batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(val_ds, batch_size=args.batch_size, shuffle=False, num_workers=0)

    device = torch.device('cpu')
    if torch.cuda.is_available():
        try:
            _ = torch.zeros(1, device='cuda')
            device = torch.device('cuda')
        except RuntimeError:
            device = torch.device('cpu')
    weights = models.MobileNet_V3_Small_Weights.IMAGENET1K_V1
    model = models.mobilenet_v3_small(weights=weights)
    in_features = model.classifier[-1].in_features
    model.classifier[-1] = nn.Linear(in_features, 2)
    model = model.to(device)

    optimizer = torch.optim.AdamW(model.parameters(), lr=args.lr, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()

    best_acc = 0.0
    for epoch in range(1, args.epochs + 1):
        model.train()
        running = 0.0
        for x, y in train_loader:
            x = x.to(device)
            y = y.to(device)
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y)
            loss.backward()
            optimizer.step()
            running += float(loss.item())

        val_acc = evaluate_val(model, val_loader, device)
        best_acc = max(best_acc, val_acc)
        print(
            f'epoch {epoch}/{args.epochs} loss={running / max(len(train_loader), 1):.4f} '
            f'val_acc={val_acc:.4f} device={device}',
            flush=True,
        )

    out_path = Path(args.out)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        'model_state': model.state_dict(),
        'model': 'mobilenet_v3_small',
        'input_size': args.input_size,
        'roi_padding': roi_padding,
        'epochs': args.epochs,
        'val_acc': round(best_acc, 4),
        'train_samples': len(train_ds),
        'val_samples': len(val_ds),
        'dataset': cfg.get('dataset_name', 'shezhenv3-coco'),
        'normalize_mean': [0.485, 0.456, 0.406],
        'normalize_std': [0.229, 0.224, 0.225],
        'tau_hint': 0.5,
    }
    torch.save(payload, out_path)

    meta = {
        'checkpoint': str(out_path),
        'val_acc': round(best_acc, 4),
        'train_images': len(train_entries),
        'train_pairs': len(train_ds),
        'val_pairs': len(val_ds),
        'device': str(device),
    }
    DEFAULT_META.write_text(json.dumps(meta, indent=2), encoding='utf-8')
    print(f'Saved B3 checkpoint -> {out_path}')
    print(json.dumps(meta, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
