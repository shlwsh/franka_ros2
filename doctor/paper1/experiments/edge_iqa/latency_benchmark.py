#!/usr/bin/env python3
"""Measure Edge-IQA CPU latency @512px (P2-T03)."""

from __future__ import annotations

import json
import statistics
import sys
import time
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.scorer import compute_q

OUT = PAPER1_ROOT / 'experiments' / 'edge_iqa' / 'latency_benchmark.json'
SYNTH = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
N_RUNS = 100


def percentile(data: list[float], p: float) -> float:
    if not data:
        return 0.0
    sorted_d = sorted(data)
    k = (len(sorted_d) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(sorted_d) - 1)
    if f == c:
        return sorted_d[f]
    return sorted_d[f] + (sorted_d[c] - sorted_d[f]) * (k - f)


def main() -> None:
    images = sorted(SYNTH.glob('clear_*.png'))[:20]
    if not images:
        raise SystemExit('run scripts/synth_degrade.py first')

    # warmup
    compute_q(images[0])

    samples = []
    idx = 0
    for _ in range(N_RUNS):
        img = images[idx % len(images)]
        idx += 1
        t0 = time.perf_counter()
        compute_q(img)
        samples.append((time.perf_counter() - t0) * 1000.0)

    report = {
        'n': N_RUNS,
        'resize': 512,
        'mean_ms': round(statistics.mean(samples), 3),
        'p50_ms': round(percentile(samples, 50), 3),
        'p95_ms': round(percentile(samples, 95), 3),
        'p99_ms': round(percentile(samples, 99), 3),
        'max_ms': round(max(samples), 3),
        'pass_p95_under_30ms': percentile(samples, 95) < 30.0,
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
    if not report['pass_p95_under_30ms']:
        raise SystemExit('p95 >= 30ms')


if __name__ == '__main__':
    main()
