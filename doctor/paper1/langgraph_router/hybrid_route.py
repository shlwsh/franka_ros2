"""Hybrid Edge Gating: Tier-A (Edge-IQA) + Tier-B (MobileNet) routing (Paper I)."""

from __future__ import annotations

EXPOSURE_FLAGS = frozenset({'underexposed', 'overexposed', 'poor_exposure'})


def hybrid_gate(
    q_b2: float,
    q_b3: float,
    flags: list[str],
    retry_count: int,
    tau_b2: float,
    tau_b3: float,
) -> tuple[float, float, str]:
    """
    Select gate score and threshold for Hybrid baseline B4.

    - Exposure failures: Tier-A (interpretable Edge-IQA + tau_b2)
    - First attempt: Tier-A fast screen
    - After resample: Tier-B blur disambiguation (MobileNet + tau_b3)
    """
    flag_set = set(flags)
    if flag_set & EXPOSURE_FLAGS:
        return q_b2, tau_b2, 'tier_a_exposure'
    if retry_count == 0:
        return q_b2, tau_b2, 'tier_a_first'
    return q_b3, tau_b3, 'tier_b_blur'
