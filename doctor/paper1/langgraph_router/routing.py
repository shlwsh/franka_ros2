"""Confidence-aware routing (Paper I §4.2)."""

from __future__ import annotations

RouteDecision = str  # upload_cloud | resample_edge | fail_safe


def route(q_img: float, retry_count: int, tau: float, K: int) -> RouteDecision:
    """
    route(s) per V19:
      upload_cloud  if Q >= tau and retry_count <= K
      resample_edge if Q < tau and retry_count <= K
      fail_safe     otherwise (retries exhausted)
    """
    if retry_count > K:
        return 'fail_safe'
    if q_img >= tau:
        return 'upload_cloud'
    return 'resample_edge'
