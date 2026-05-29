"""CLI: run closed-loop trials and append JSONL."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def _paper1_root() -> Path:
    return Path(__file__).resolve().parents[1]


def _append_jsonl(log_path: Path, record: dict) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open('a', encoding='utf-8') as f:
        f.write(json.dumps(record, ensure_ascii=False) + '\n')


def main() -> int:
    parser = argparse.ArgumentParser(description='Paper I closed-loop trials')
    parser.add_argument('--trials', type=int, default=10)
    parser.add_argument('--log', type=str, default='experiments/logs/run_001.jsonl')
    parser.add_argument('--api-base', type=str, default='')
    parser.add_argument('--api-key', type=str, default='')
    parser.add_argument('--tau', type=float, default=None)
    parser.add_argument('--K', type=int, default=2)
    parser.add_argument('--use-api-iqa', action='store_true')
    parser.add_argument('--use-api-motion', action='store_true')
    args = parser.parse_args()

    root = _paper1_root()
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))

    from langgraph_router.graph import build_trial_image_list, run_trial

    log_path = Path(args.log)
    if not log_path.is_absolute():
        log_path = root / log_path
    if log_path.exists():
        log_path.unlink()

    client = None
    if args.api_base:
        from sim.franka_bridge.client import FrankaApiClient

        client = FrankaApiClient(
            base_url=args.api_base,
            api_key=args.api_key or __import__('os').environ.get('FRANKA_API_KEY', 'franka-api-default-key'),
        )
        try:
            client.health_joints()
        except Exception as exc:
            print(f'warning: API health check failed: {exc}', file=sys.stderr)

    images = build_trial_image_list(root, args.trials)
    decisions = set()

    for tid, img in enumerate(images, start=1):
        if not img.is_file():
            raise SystemExit(f'missing image {img}; run scripts/synth_degrade.py')
        state = run_trial(
            tid,
            img,
            paper1_root=root,
            tau=args.tau,
            K=args.K,
            api_client=client if args.use_api_motion else None,
            use_api_iqa=args.use_api_iqa and client is not None,
        )
        record = dict(state)
        _append_jsonl(log_path, record)
        decisions.add(record['route_decision'])
        print(f"trial {tid}: q={record['q_img']} -> {record['route_decision']}")

    if client:
        client.close()

    print(f'Wrote {args.trials} lines -> {log_path}')
    print(f'route decisions seen: {sorted(decisions)}')
    required = {'upload_cloud', 'resample_edge'}
    if not required.issubset(decisions):
        print(f'warning: expected both upload_cloud and resample_edge in {args.trials} trials')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
