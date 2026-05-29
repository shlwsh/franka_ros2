#!/usr/bin/env python3
"""Validate Paper I closed-loop JSONL schema."""

from __future__ import annotations

import json
import sys
from pathlib import Path

REQUIRED = (
    'trial_id',
    'image_path',
    'q_img',
    'flags',
    'retry_count',
    'route_decision',
    't_capture',
    't_iqa',
    't_route',
    'latency_ms',
)
VALID_ROUTES = {'upload_cloud', 'resample_edge', 'fail_safe'}


def main() -> int:
    if len(sys.argv) < 2:
        print('usage: validate_jsonl.py <path.jsonl>', file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    if not path.is_file():
        print(f'missing: {path}', file=sys.stderr)
        return 1

    lines = path.read_text(encoding='utf-8').strip().splitlines()
    if len(lines) < 10:
        print(f'FAIL: need >=10 lines, got {len(lines)}')
        return 1

    routes = set()
    for i, line in enumerate(lines, 1):
        row = json.loads(line)
        missing = [k for k in REQUIRED if k not in row]
        if missing:
            print(f'FAIL line {i}: missing {missing}')
            return 1
        if row['route_decision'] not in VALID_ROUTES:
            print(f'FAIL line {i}: bad route {row["route_decision"]}')
            return 1
        if '..' in row['image_path'] or row['image_path'].startswith('/'):
            print(f'FAIL line {i}: image_path must be relative: {row["image_path"]}')
            return 1
        routes.add(row['route_decision'])

    print(f'OK: {len(lines)} lines, routes={sorted(routes)}')
    if not {'upload_cloud', 'resample_edge'}.issubset(routes):
        print('WARN: expected upload_cloud and resample_edge in batch')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
