"""Readiness probe for franka_api_server Paper II integration."""

from __future__ import annotations

import argparse
import json
from typing import Any

from doctor.paper2.tools.franka_client import FrankaApiClient, FrankaApiError


def probe(client: FrankaApiClient) -> dict[str, Any]:
    result: dict[str, Any] = {
        "base_url": client.base_url,
        "status": "offline",
        "joints_ok": False,
        "skills_ok": False,
        "skills": [],
        "errors": [],
    }
    try:
        joints = client.health_joints()
        result["joints_ok"] = True
        result["joints_keys"] = sorted(joints.keys())
    except FrankaApiError as exc:
        result["errors"].append(f"joints: {exc}")

    try:
        skills = client.list_skills()
        result["skills_ok"] = True
        result["skills"] = list(skills.get("skills", []))
    except FrankaApiError as exc:
        result["errors"].append(f"skills: {exc}")

    if result["joints_ok"] and result["skills_ok"]:
        result["status"] = "online"
    elif result["joints_ok"] or result["skills_ok"]:
        result["status"] = "partial"
    return result


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--timeout-s", type=float, default=3.0)
    args = parser.parse_args()

    default_client = FrankaApiClient()
    client = FrankaApiClient(
        base_url=args.base_url or default_client.base_url,
        api_key=args.api_key or default_client.api_key,
        timeout_s=args.timeout_s,
    )
    print(json.dumps(probe(client), ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
