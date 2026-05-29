"""Routing unit tests (no API / ROS)."""

from __future__ import annotations

import sys
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

from langgraph_router.routing import route


def test_route_upload():
    assert route(q_img=0.8, retry_count=0, tau=0.55, K=2) == 'upload_cloud'


def test_route_resample():
    assert route(q_img=0.3, retry_count=0, tau=0.55, K=2) == 'resample_edge'


def test_route_fail_safe():
    assert route(q_img=0.3, retry_count=3, tau=0.55, K=2) == 'fail_safe'


def test_route_at_tau_boundary():
    assert route(q_img=0.55, retry_count=0, tau=0.55, K=2) == 'upload_cloud'
