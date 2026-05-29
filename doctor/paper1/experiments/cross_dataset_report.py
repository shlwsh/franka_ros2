#!/usr/bin/env python3
"""M5: cross-cohort quality correlation (synthetic clear/blur as proxy)."""

from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np

PAPER1_ROOT = Path(__file__).resolve().parents[1]


def spearman(x, y):
    rx = np.argsort(np.argsort(x))
    ry = np.argsort(np.argsort(y))
    if len(x) < 2:
        return 0.0
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> None:
    val_csv = PAPER1_ROOT / 'experiments/results/calibration_val.csv'
    if not val_csv.is_file():
        raise SystemExit('run calibrate_tau first (calibration_val.csv)')

    labels, scores = [], []
    with val_csv.open(encoding='utf-8') as f:
        for row in csv.DictReader(f):
            labels.append(1 if row['label'] == 'clear' else 0)
            scores.append(float(row['q_img']))

    rho = spearman(np.array(scores), np.array(labels))
    out_csv = PAPER1_ROOT / 'experiments/results/cross_tcm_fd.csv'
    with out_csv.open('w', newline='', encoding='utf-8') as f:
        w = csv.writer(f)
        w.writerow(['metric', 'value', 'note'])
        w.writerow(['spearman_q_vs_label', round(rho, 4), 'synthetic val n=240'])
        w.writerow(['n_samples', len(scores), 'placeholder for TCM full set'])

    summary = {'spearman': round(rho, 4), 'n': len(scores)}
    (PAPER1_ROOT / 'experiments/results/cross_tcm_fd.json').write_text(
        json.dumps(summary, indent=2), encoding='utf-8'
    )
    print(f'Wrote {out_csv} spearman={rho:.4f}')


if __name__ == '__main__':
    main()
