"""Learned B3 IQA scorer (MobileNet fine-tuned on ShezhenV3 train split)."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List, Sequence

import numpy as np
from PIL import Image

from edge_iqa.coco_roi import bbox_from_entry, crop_roi

DEFAULT_CHECKPOINT = (
    Path(__file__).resolve().parents[1] / 'experiments/results/b3_mobilenet.pt'
)


@dataclass
class LearnedResult:
    q_img: float
    flags: List[str]
    t_iqa_ms: float
    prob_clear: float

    def to_dict(self) -> dict:
        return {
            'q_img': round(self.q_img, 4),
            'flags': self.flags,
            't_iqa_ms': round(self.t_iqa_ms, 3),
            'prob_clear': round(self.prob_clear, 4),
        }


class LearnedB3Scorer:
    def __init__(self, checkpoint: str | Path = DEFAULT_CHECKPOINT):
        import torch
        from torchvision import models, transforms

        self._torch = torch
        ckpt_path = Path(checkpoint)
        if not ckpt_path.is_file():
            raise FileNotFoundError(f'B3 checkpoint not found: {ckpt_path}')

        payload = torch.load(ckpt_path, map_location='cpu', weights_only=False)
        self.input_size = int(payload.get('input_size', 224))
        self.tau_hint = float(payload.get('tau_hint', 0.5))
        self.roi_padding = float(payload.get('roi_padding', 0.08))

        model = models.mobilenet_v3_small(weights=None)
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = torch.nn.Linear(in_features, 2)
        model.load_state_dict(payload['model_state'])
        model.eval()
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        self.model = model.to(self.device)

        mean = payload.get('normalize_mean', [0.485, 0.456, 0.406])
        std = payload.get('normalize_std', [0.229, 0.224, 0.225])
        self.transform = transforms.Compose(
            [
                transforms.Resize((self.input_size, self.input_size)),
                transforms.ToTensor(),
                transforms.Normalize(mean=mean, std=std),
            ]
        )

    def _prepare(
        self,
        image: Image.Image,
        bboxes: Sequence[Sequence[float]] | None,
    ) -> Image.Image:
        im = image.convert('RGB')
        if bboxes:
            im = crop_roi(im, bboxes, padding=self.roi_padding)
        return im

    def score_pil(
        self,
        image: Image.Image,
        *,
        bboxes: Sequence[Sequence[float]] | None = None,
    ) -> LearnedResult:
        t0 = time.perf_counter()
        prepared = self._prepare(image, bboxes)
        tensor = self.transform(prepared).unsqueeze(0).to(self.device)
        with self._torch.no_grad():
            logits = self.model(tensor)
            probs = self._torch.softmax(logits, dim=1)[0]
            prob_clear = float(probs[1].cpu().item())

        q = float(np.clip(prob_clear, 0.0, 1.0))
        flags: List[str] = []
        if q < self.tau_hint:
            flags.append('blur')
        elapsed_ms = (time.perf_counter() - t0) * 1000.0
        return LearnedResult(
            q_img=q,
            flags=flags,
            t_iqa_ms=elapsed_ms,
            prob_clear=prob_clear,
        )

    def score_bytes(
        self,
        data: bytes,
        *,
        bboxes: Sequence[Sequence[float]] | None = None,
    ) -> LearnedResult:
        import io

        with Image.open(io.BytesIO(data)) as im:
            return self.score_pil(im, bboxes=bboxes)

    def score_entry(self, entry: dict, raw: bytes | None = None) -> LearnedResult:
        path = Path(entry['path'])
        bboxes = bbox_from_entry(entry)
        if raw is None:
            raw = path.read_bytes()
        return self.score_bytes(raw, bboxes=bboxes)


_scorer: LearnedB3Scorer | None = None


def get_learned_scorer(checkpoint: str | Path | None = None) -> LearnedB3Scorer:
    global _scorer
    if _scorer is None or checkpoint is not None:
        ckpt = checkpoint or DEFAULT_CHECKPOINT
        _scorer = LearnedB3Scorer(ckpt)
    return _scorer


def score_bytes_b3(
    data: bytes,
    *,
    bboxes: Sequence[Sequence[float]] | None = None,
    checkpoint: str | Path | None = None,
) -> LearnedResult:
    return get_learned_scorer(checkpoint).score_bytes(data, bboxes=bboxes)


def load_training_meta(checkpoint: str | Path = DEFAULT_CHECKPOINT) -> dict:
    import torch

    payload = torch.load(checkpoint, map_location='cpu', weights_only=False)
    return {
        'epochs': payload.get('epochs'),
        'val_acc': payload.get('val_acc'),
        'train_samples': payload.get('train_samples'),
        'val_samples': payload.get('val_samples'),
        'dataset': payload.get('dataset'),
        'model': payload.get('model', 'mobilenet_v3_small'),
    }
