"""CLI for subprocess / edge gateway: python -m edge_iqa.cli --image PATH --json"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description='Edge-IQA scorer CLI')
    parser.add_argument('--image', required=True, help='Path to PNG/JPEG')
    parser.add_argument('--json', action='store_true', help='Print JSON to stdout')
    parser.add_argument('--resize', type=int, default=512)
    args = parser.parse_args()

    # Ensure doctor/paper1 is importable when run as module from repo root
    paper1_root = Path(__file__).resolve().parents[1]
    if str(paper1_root) not in sys.path:
        sys.path.insert(0, str(paper1_root))

    from edge_iqa.scorer import compute_q

    result = compute_q(args.image, resize=args.resize)
    payload = result.to_dict()
    payload['meta'] = {'scorer': 'edge_iqa', 'version': '0.2.0'}

    if args.json:
        print(json.dumps(payload))
    else:
        print(payload)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
