"""Collect and validate Paper II Franka API closed-loop evidence.

The collector requires a live ``franka_api_server``. It probes joint/skill
endpoints, executes named skills through the HTTP tool surface, and writes a CSV
that the readiness audit can validate. Offline synthetic experiments do not call
this script.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from doctor.paper2.tools.franka_client import FrankaApiClient, FrankaApiError
from doctor.paper2.tools.franka_probe import probe

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "franka_closed_loop.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "franka_closed_loop_report.md"
DEFAULT_MIN_SUCCESS = 1
REQUIRED_COLUMNS = {
    "trial_id",
    "base_url",
    "probe_status",
    "skill_name",
    "skill_success",
    "latency_ms",
    "joints_ok",
    "skills_ok",
    "error",
}


@dataclass(frozen=True)
class ClosedLoopValidation:
    ready: bool
    rows: int
    successes: int
    reason: str


def _skill_names(value: str | None) -> list[str]:
    if not value:
        return ["go_to_tongue_pose"]
    names = [item.strip() for item in value.split(",") if item.strip()]
    if not names:
        raise ValueError("at least one skill name is required")
    return names


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "trial_id",
        "base_url",
        "probe_status",
        "skill_name",
        "skill_success",
        "latency_ms",
        "joints_ok",
        "skills_ok",
        "error",
        "response_json",
    ]
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def _write_report(path: Path, rows: list[dict[str, Any]], validation: ClosedLoopValidation) -> None:
    lines = [
        "# Franka Closed-Loop Report",
        "",
        "Evidence collected through franka_api_server HTTP tool calls.",
        "",
        f"- rows: {validation.rows}",
        f"- successes: {validation.successes}",
        f"- ready: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Trial | Probe | Skill | Success | Latency ms | Error |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['trial_id']} | {row['probe_status']} | {row['skill_name']} | "
            f"{row['skill_success']} | {row['latency_ms']} | {row['error']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect(
    *,
    client: FrankaApiClient,
    trials: int,
    skill_names: list[str],
) -> list[dict[str, Any]]:
    if trials < 1:
        raise ValueError("trials must be >= 1")
    probe_result = probe(client)
    if probe_result["status"] != "online":
        raise FrankaApiError(f"franka_api_server probe is not online: {probe_result}")

    available_skills = set(str(item) for item in probe_result.get("skills", []))
    missing = [skill for skill in skill_names if skill not in available_skills]
    if missing:
        raise FrankaApiError(f"requested skill(s) are not available: {', '.join(missing)}")

    rows: list[dict[str, Any]] = []
    for idx in range(trials):
        skill_name = skill_names[idx % len(skill_names)]
        started = time.perf_counter()
        error = ""
        response: dict[str, Any] = {}
        success = False
        try:
            response = client.go_to_skill(skill_name)
            success = True
        except FrankaApiError as exc:
            error = str(exc)
        latency_ms = round((time.perf_counter() - started) * 1000.0, 4)
        rows.append(
            {
                "trial_id": f"franka_{idx:04d}",
                "base_url": client.base_url,
                "probe_status": probe_result["status"],
                "skill_name": skill_name,
                "skill_success": success,
                "latency_ms": latency_ms,
                "joints_ok": bool(probe_result.get("joints_ok")),
                "skills_ok": bool(probe_result.get("skills_ok")),
                "error": error,
                "response_json": json.dumps(response, sort_keys=True),
            }
        )
    return rows


def validate_closed_loop_csv(
    path: Path = DEFAULT_OUT,
    *,
    min_successes: int = DEFAULT_MIN_SUCCESS,
) -> ClosedLoopValidation:
    if not path.is_file():
        return ClosedLoopValidation(False, 0, 0, f"closed-loop CSV not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing:
            return ClosedLoopValidation(False, 0, 0, f"missing column(s): {', '.join(sorted(missing))}")
        rows = list(reader)
    if not rows:
        return ClosedLoopValidation(False, 0, 0, "closed-loop CSV has no rows")
    successes = 0
    for row in rows:
        if row.get("probe_status") != "online":
            return ClosedLoopValidation(False, len(rows), successes, "probe_status is not online")
        if str(row.get("joints_ok", "")).lower() != "true":
            return ClosedLoopValidation(False, len(rows), successes, "joints_ok is not true")
        if str(row.get("skills_ok", "")).lower() != "true":
            return ClosedLoopValidation(False, len(rows), successes, "skills_ok is not true")
        try:
            latency_ms = float(row.get("latency_ms", ""))
        except ValueError:
            return ClosedLoopValidation(False, len(rows), successes, "latency_ms is not numeric")
        if latency_ms < 0:
            return ClosedLoopValidation(False, len(rows), successes, "latency_ms is negative")
        if str(row.get("skill_success", "")).lower() == "true":
            successes += 1
    if successes < min_successes:
        return ClosedLoopValidation(
            False,
            len(rows),
            successes,
            f"successful skill calls {successes} below required {min_successes}",
        )
    return ClosedLoopValidation(True, len(rows), successes, "closed-loop evidence passed validation")


def run(
    *,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
    base_url: str | None = None,
    api_key: str | None = None,
    timeout_s: float = 5.0,
    trials: int = 3,
    skill_names: list[str] | None = None,
) -> ClosedLoopValidation:
    default_client = FrankaApiClient()
    client = FrankaApiClient(
        base_url=base_url or default_client.base_url,
        api_key=api_key or default_client.api_key,
        timeout_s=timeout_s,
    )
    rows = collect(client=client, trials=trials, skill_names=skill_names or ["go_to_tongue_pose"])
    _write_csv(out_path, rows)
    validation = validate_closed_loop_csv(out_path)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    parser.add_argument("--base-url", default=None)
    parser.add_argument("--api-key", default=None)
    parser.add_argument("--timeout-s", type=float, default=5.0)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--skills", default=None, help="Comma-separated skill names to execute")
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--min-successes", type=int, default=DEFAULT_MIN_SUCCESS)
    args = parser.parse_args()

    if args.validate_only:
        validation = validate_closed_loop_csv(args.out, min_successes=args.min_successes)
    else:
        validation = run(
            out_path=args.out,
            report_path=args.report,
            base_url=args.base_url,
            api_key=args.api_key,
            timeout_s=args.timeout_s,
            trials=args.trials,
            skill_names=_skill_names(args.skills),
        )
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
