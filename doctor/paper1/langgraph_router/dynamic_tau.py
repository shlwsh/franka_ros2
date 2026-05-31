"""Dynamic confidence threshold: tau_t = tau_0 + alpha * RTT_norm + beta * P_loss."""

from __future__ import annotations


def dynamic_tau(
    tau_0: float,
    rtt_ms: float,
    p_loss: float,
    *,
    alpha: float = 0.08,
    beta: float = 0.25,
    rtt_ref_ms: float = 300.0,
    tau_min: float = 0.05,
    tau_max: float = 0.95,
) -> float:
    """Raise threshold under poor network (higher RTT / loss) to avoid bad uploads."""
    rtt_norm = rtt_ms / max(rtt_ref_ms, 1.0)
    tau_t = tau_0 + alpha * rtt_norm + beta * p_loss
    return min(tau_max, max(tau_min, tau_t))
