#!/usr/bin/env python3
"""M5: cross-cohort quality correlation on ShezhenV3 calibration CSV."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

PAPER1_ROOT = Path(__file__).resolve().parents[1]
import sys

sys.path.insert(0, str(PAPER1_ROOT))
from paper1_trace import init_trace, trace_call


@trace_call()
def spearman(x, y):
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    if len(x) < 2:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


@trace_call()
def main() -> None:
    init_trace(__file__)
    import logging

    log = logging.getLogger('paper1.cross_dataset_report')
    val_csv = PAPER1_ROOT / 'experiments/results/calibration_val.csv'
    if not val_csv.is_file():
        raise SystemExit('run calibrate_tau_tcm.py first (calibration_val.csv)')

    labels, scores = [], []
    with val_csv.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            labels.append(1 if row['label'] == 'clear' else 0)
            scores.append(float(row['q_img']))

    rho = spearman(np.array(scores), np.array(labels))
    source = 'shezhenv3-coco'
    with val_csv.open(encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        if rows and rows[0].get('source'):
            source = rows[0]['source']

    out_csv = PAPER1_ROOT / 'experiments/results/cross_tcm_fd.csv'
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value', 'note'])
        w.writerow(['spearman_q_vs_label', round(rho, 4), f'{source} val n={len(scores)}'])
        w.writerow(['n_samples', len(scores), source])

    summary = {'spearman': round(rho, 4), 'n': len(scores), 'dataset': source}
    (PAPER1_ROOT / 'experiments/results/cross_tcm_fd.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    log.info('Wrote %s spearman=%s n=%s', out_csv, rho, len(scores))
    print(f'Wrote {out_csv} spearman={rho:.4f} n={len(scores)}')


if __name__ == '__main__':
    main()
