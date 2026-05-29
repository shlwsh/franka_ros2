#!/usr/bin/env python3
"""Calibrate routing threshold tau from val split."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
if str(PAPER1_ROOT) not in sys.path:
    sys.path.insert(0, str(PAPER1_ROOT))

from edge_iqa.scorer import compute_q

VAL_JSON = PAPER1_ROOT / 'experiments' / 'splits' / 'val.json'
OUT_CSV = PAPER1_ROOT / 'experiments' / 'results' / 'calibration_val.csv'
OUT_TAU = PAPER1_ROOT / 'experiments' / 'results' / 'recommended_tau.json'


def main() -> None:
    if not VAL_JSON.is_file():
        raise SystemExit(f'missing {VAL_JSON}; run scripts/synth_degrade.py first')

    entries = json.loads(VAL_JSON.read_text(encoding='utf-8'))
    rows = []
    clear_q, blur_q = [], []

    for item in entries:
        path = PAPER1_ROOT / item['path']
        label = item.get('label', 'unknown')
        r = compute_q(path)
        rows.append(
            {
                'path': item['path'],
                'label': label,
                'q_img': r.q_img,
                'flags': ';'.join(r.flags),
            }
        )
        if label == 'clear':
            clear_q.append(r.q_img)
        elif label == 'blur':
            blur_q.append(r.q_img)

    # Midpoint between class medians (clamped)
    import statistics

    med_clear = statistics.median(clear_q) if clear_q else 0.7
    med_blur = statistics.median(blur_q) if blur_q else 0.3
    tau = round((med_clear + med_blur) / 2.0, 3)
    tau = max(0.45, min(0.65, tau))

    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['path', 'label', 'q_img', 'flags'])
        writer.writeheader()
        writer.writerows(rows)

    OUT_TAU.write_text(
        json.dumps(
            {
                'tau': tau,
                'median_clear': med_clear,
                'median_blur': med_blur,
                'n_val': len(rows),
            },
            indent=2,
        ),
        encoding='utf-8',
    )
    print(f'Wrote {OUT_CSV} ({len(rows)} rows)')
    print(f'Recommended tau={tau} -> {OUT_TAU}')


if __name__ == '__main__':
    main()
