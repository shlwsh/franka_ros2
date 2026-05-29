"""Bridge to doctor/paper1 edge_iqa (subprocess or in-process)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

from fastapi import HTTPException

from ..config import settings
from ..models.vision import VisionEvaluateResponse


def _paper1_root() -> Path:
    root = Path(settings.paper1_root)
    if not root.is_dir():
        raise HTTPException(
            status_code=503,
            detail=f'PAPER1_ROOT not found: {root}',
        )
    return root


def _load_tau() -> float:
    tau_file = _paper1_root() / 'experiments' / 'results' / 'recommended_tau.json'
    if tau_file.is_file():
        try:
            data = json.loads(tau_file.read_text(encoding='utf-8'))
            return float(data.get('tau', settings.vision_threshold_tau))
        except (json.JSONDecodeError, TypeError, ValueError):
            pass
    return settings.vision_threshold_tau


def _evaluate_subprocess(image_path: Path) -> VisionEvaluateResponse:
    root = _paper1_root()
    cmd = [
        sys.executable,
        '-m',
        'edge_iqa.cli',
        '--image',
        str(image_path.resolve()),
        '--json',
    ]
    env = os.environ.copy()
    env['PYTHONPATH'] = str(root) + os.pathsep + env.get('PYTHONPATH', '')
    try:
        proc = subprocess.run(
            cmd,
            cwd=str(root),
            env=env,
            capture_output=True,
            text=True,
            timeout=settings.iqa_timeout_s,
            check=False,
        )
    except subprocess.TimeoutExpired as exc:
        raise HTTPException(status_code=504, detail='edge_iqa timeout') from exc

    if proc.returncode != 0:
        raise HTTPException(
            status_code=503,
            detail=f'edge_iqa failed: {proc.stderr.strip() or proc.stdout}',
        )

    try:
        payload = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError) as exc:
        raise HTTPException(status_code=503, detail='invalid edge_iqa JSON') from exc

    meta = payload.get('meta') or {}
    if isinstance(meta, dict):
        meta.setdefault('scorer', 'edge_iqa')
        meta.setdefault('mode', 'subprocess')
    else:
        meta = {'scorer': 'edge_iqa', 'mode': 'subprocess'}

    return VisionEvaluateResponse(
        q_img=float(payload['q_img']),
        flags=list(payload.get('flags') or []),
        t_iqa_ms=float(payload.get('t_iqa_ms', 0.0)),
        threshold_tau=_load_tau(),
        meta={str(k): str(v) for k, v in meta.items()},
    )


def _evaluate_inprocess(image_path: Path) -> VisionEvaluateResponse:
    root = str(_paper1_root())
    if root not in sys.path:
        sys.path.insert(0, root)
    from edge_iqa.scorer import compute_q

    result = compute_q(image_path)
    return VisionEvaluateResponse(
        q_img=result.q_img,
        flags=result.flags,
        t_iqa_ms=result.t_iqa_ms,
        threshold_tau=_load_tau(),
        meta={'scorer': 'edge_iqa', 'version': '0.2.0', 'mode': 'import'},
    )


def evaluate_image_path(image_path: Path) -> VisionEvaluateResponse:
    if not image_path.is_file():
        raise HTTPException(status_code=400, detail=f'image not found: {image_path}')

    scorer_py = _paper1_root() / 'edge_iqa' / 'scorer.py'
    if not scorer_py.is_file():
        return VisionEvaluateResponse(
            q_img=settings.vision_placeholder_q,
            flags=[],
            t_iqa_ms=0.1,
            threshold_tau=settings.vision_threshold_tau,
            meta={'scorer': 'placeholder', 'reason': 'edge_iqa not installed'},
        )

    if settings.iqa_subprocess:
        return _evaluate_subprocess(image_path)
    return _evaluate_inprocess(image_path)


def evaluate_image_bytes(data: bytes, *, saved_path: Optional[Path] = None) -> VisionEvaluateResponse:
    if saved_path is not None and saved_path.is_file():
        return evaluate_image_path(saved_path)

    root = _paper1_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from edge_iqa.scorer import compute_q_from_bytes

    result = compute_q_from_bytes(data)
    return VisionEvaluateResponse(
        q_img=result.q_img,
        flags=result.flags,
        t_iqa_ms=result.t_iqa_ms,
        threshold_tau=_load_tau(),
        meta={'scorer': 'edge_iqa', 'version': '0.2.0', 'mode': 'bytes'},
    )
