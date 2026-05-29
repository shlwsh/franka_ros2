#!/usr/bin/env python3
"""Summarize M6 trials from JSONL to franka_m6_rtt.csv."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list, p: float) -> float:
    if not values:
        return 0.0
    s = sorted(values)
    k = (len(s) - 1) * p / 100.0
    f = int(k)
    c = min(f + 1, len(s) - 1)
    if f == c:
        return s[f]
    return s[f] + (s[c] - s[f]) * (k - f)


def main() -> int:
    jsonl = Path(sys.argv[1]) if len(sys.argv) > 1 else PAPER1_ROOT / 'experiments/logs/m6_run.jsonl'
    out = PAPER1_ROOT / 'experiments/results/franka_m6_rtt.csv'
    if not jsonl.is_file():
        raise SystemExit(f'missing {jsonl}')

    rows = []
    for line in jsonl.read_text(encoding='utf-8').splitlines():
        if line.strip():
            rows.append(json.loads(line))

    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open('w', newline='', encoding='utf-8') as f:
        w = csv.DictWriter(
            f,
            fieldnames=['trial_id', 'latency_ms', 'route_decision', 'retry_count', 'q_img'],
        )
        w.writeheader()
        for r in rows:
            w.writerow(
                {
                    'trial_id': r['trial_id'],
                    'latency_ms': r['latency_ms'],
                    'route_decision': r['route_decision'],
                    'retry_count': r['retry_count'],
                    'q_img': r['q_img'],
                }
            )

    lats = [float(r['latency_ms']) for r in rows]
    summary = {
        'n': len(rows),
        'p50_ms': round(percentile(lats, 50), 2),
        'p95_ms': round(percentile(lats, 95), 2),
        'mean_ms': round(sum(lats) / len(lats), 2),
    }
    (PAPER1_ROOT / 'experiments/results/franka_m6_summary.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    print(f'Wrote {out} ({len(rows)} rows)')
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
