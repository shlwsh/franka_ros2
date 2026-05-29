"""Closed-loop trial graph: capture → edge_iqa → route → action."""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

from edge_iqa.scorer import compute_q

from .routing import route
from .state import TrialState


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')


def _load_tau(paper1_root: Path) -> float:
    p = paper1_root / 'experiments' / 'results' / 'recommended_tau.json'
    if p.is_file():
        data = json.loads(p.read_text(encoding='utf-8'))
        return float(data.get('tau', 0.55))
    return 0.55


def run_trial(
    trial_id: int,
    image_path: Path,
    *,
    paper1_root: Path,
    tau: Optional[float] = None,
    K: int = 2,
    retry_count: int = 0,
    api_client: Optional[Any] = None,
    use_api_iqa: bool = False,
    on_resample: Optional[Callable[[], None]] = None,
) -> TrialState:
    """Execute one capture→iqa→route cycle; optional resample skill via API."""
    tau = tau if tau is not None else _load_tau(paper1_root)
    rel_path = str(image_path.relative_to(paper1_root))

    t_capture = _utc_now()
    t0 = time.perf_counter()

    if use_api_iqa and api_client is not None:
        iqa = api_client.evaluate_image(image_path)
        q_img = float(iqa['q_img'])
        flags = list(iqa.get('flags') or [])
        t_iqa = _utc_now()
    else:
        result = compute_q(image_path)
        q_img = result.q_img
        flags = result.flags
        t_iqa = _utc_now()

    decision = route(q_img, retry_count, tau, K)
    t_route = _utc_now()

    if decision == 'resample_edge' and api_client is not None:
        try:
            api_client.go_to_skill('go_to_tongue_pose')
        except Exception:
            pass  # motion optional without ROS stack
        if on_resample:
            on_resample()

    latency_ms = (time.perf_counter() - t0) * 1000.0

    return TrialState(
        trial_id=trial_id,
        image_path=rel_path,
        q_img=round(q_img, 4),
        flags=flags,
        retry_count=retry_count,
        route_decision=decision,
        t_capture=t_capture,
        t_iqa=t_iqa,
        t_route=t_route,
        latency_ms=round(latency_ms, 2),
    )


def build_trial_image_list(paper1_root: Path, n: int) -> list[Path]:
    """Alternate clear/blur synthetic images so both routes appear."""
    clear_dir = paper1_root / 'experiments' / 'synthetic' / 'clear'
    blur_dir = paper1_root / 'experiments' / 'synthetic' / 'blur'
    paths: list[Path] = []
    for i in range(n):
        if i % 2 == 0:
            paths.append(clear_dir / f'clear_{i % 120:04d}.png')
        else:
            paths.append(blur_dir / f'blur_{i % 120:04d}.png')
    return paths
