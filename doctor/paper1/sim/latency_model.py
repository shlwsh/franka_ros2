"""Offline network / motion latency sampling for main experiment simulation."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass


@dataclass
class LatencyConfig:
    capture_ms: float = 5.0
    edge_iqa_ms_mean: float = 9.0
    edge_iqa_ms_std: float = 2.0
    route_ms: float = 1.5
    resample_mu: float = 6.7
    resample_sigma: float = 0.35
    cloud_min: float = 50.0
    cloud_max: float = 550.0


def sample_edge_iqa_ms(rng: random.Random, cfg: LatencyConfig) -> float:
    return max(1.0, rng.gauss(cfg.edge_iqa_ms_mean, cfg.edge_iqa_ms_std))


def sample_resample_ms(rng: random.Random, cfg: LatencyConfig) -> float:
    """Edge re-capture latency (offline main track); full-arm motion is M6 auxiliary."""
    return max(15.0, rng.lognormvariate(cfg.resample_mu, cfg.resample_sigma))


def sample_cloud_upload_ms(rng: random.Random, cfg: LatencyConfig) -> float:
    return rng.uniform(cfg.cloud_min, cfg.cloud_max)
