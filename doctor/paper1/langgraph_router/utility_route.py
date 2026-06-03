"""Quality-aware utility routing: U = w1*Q - w2*RTT_norm - w3*Cost."""

from __future__ import annotations

RouteDecision = str  # upload_cloud | resample_edge | fail_safe


def compute_utility(
    q: float,
    rtt_ms: float,
    cost: float,
    *,
    w1: float,
    w2: float,
    w3: float,
    rtt_ref_ms: float = 300.0,
) -> float:
    rtt_norm = rtt_ms / max(rtt_ref_ms, 1.0)
    return w1 * q - w2 * rtt_norm - w3 * cost


def utility_route(
    q: float,
    rtt_ms: float,
    retry_count: int,
    K: int,
    *,
    u_threshold: float,
    w1: float = 1.0,
    w2: float = 0.15,
    w3: float = 0.35,
    resample_cost: float = 1.0,
    rtt_ref_ms: float = 300.0,
) -> RouteDecision:
    """
    Upload when U(Q, RTT, cost=0) >= u_threshold; else resample until budget K.
    """
    if retry_count > K:
        return 'fail_safe'
    u = compute_utility(
        q,
        rtt_ms,
        0.0,
        w1=w1,
        w2=w2,
        w3=w3,
        rtt_ref_ms=rtt_ref_ms,
    )
    if u >= u_threshold:
        return 'upload_cloud'
    return 'resample_edge'
