"""Multi-frame Edge-IQA fusion via exponential moving average."""

from __future__ import annotations

import random


def ema_quality(q_prev: float | None, q_new: float, lam: float) -> float:
    """Q_t = lam * Q_{t-1} + (1 - lam) * Q_new."""
    if q_prev is None:
        return q_new
    return lam * q_prev + (1.0 - lam) * q_new


def fuse_burst_scores(
    scores: list[float],
    lam: float,
) -> float:
    """Fuse an ordered burst of per-frame scores."""
    fused: float | None = None
    for s in scores:
        fused = ema_quality(fused, s, lam)
    assert fused is not None
    return fused


def simulate_burst_scores(
    q_center: float,
    n_frames: int,
    rng: random.Random,
    *,
    noise_std: float = 0.025,
) -> list[float]:
    """Offline micro-burst: jitter around center score (models consecutive captures)."""
    out = []
    for _ in range(n_frames):
        q = q_center + rng.gauss(0.0, noise_std)
        out.append(min(1.0, max(0.0, q)))
    return out
