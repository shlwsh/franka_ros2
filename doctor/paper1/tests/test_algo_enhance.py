"""Tests for Paper I algorithm enhancements (dynamic tau, EMA, utility)."""

from __future__ import annotations

import random
import sys
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from langgraph_router.dynamic_tau import dynamic_tau
from langgraph_router.multi_frame_iqa import ema_quality, fuse_burst_scores, simulate_burst_scores
from langgraph_router.utility_route import compute_utility, utility_route


def test_dynamic_tau_increases_with_rtt():
    low = dynamic_tau(0.45, rtt_ms=100.0, p_loss=0.0)
    high = dynamic_tau(0.45, rtt_ms=500.0, p_loss=0.0)
    assert high > low


def test_dynamic_tau_increases_with_loss():
    low = dynamic_tau(0.45, rtt_ms=200.0, p_loss=0.0)
    high = dynamic_tau(0.45, rtt_ms=200.0, p_loss=0.2)
    assert high > low


def test_dynamic_tau_clamped():
    t = dynamic_tau(0.45, rtt_ms=5000.0, p_loss=1.0, tau_max=0.95)
    assert t <= 0.95


def test_ema_first_frame():
    assert ema_quality(None, 0.5, 0.6) == 0.5


def test_ema_smoothing():
    fused = fuse_burst_scores([0.4, 0.5, 0.6], lam=0.5)
    assert 0.45 <= fused <= 0.55


def test_burst_scores_bounded():
    rng = random.Random(0)
    scores = simulate_burst_scores(0.5, 5, rng)
    assert all(0.0 <= s <= 1.0 for s in scores)


def test_utility_upload_high_quality():
    assert utility_route(0.9, 100.0, 0, 2, u_threshold=0.3) == 'upload_cloud'


def test_utility_resample_low_quality():
    assert utility_route(0.2, 400.0, 0, 2, u_threshold=0.5) == 'resample_edge'


def test_utility_fail_safe():
    assert utility_route(0.2, 400.0, 3, 2, u_threshold=0.5) == 'fail_safe'


def test_compute_utility_decreases_with_rtt():
    u_low = compute_utility(0.6, 100.0, 0.0, w1=1.0, w2=0.2, w3=0.1)
    u_high = compute_utility(0.6, 500.0, 0.0, w1=1.0, w2=0.2, w3=0.1)
    assert u_low > u_high
