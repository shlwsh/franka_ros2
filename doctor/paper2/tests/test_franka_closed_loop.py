import csv
from pathlib import Path

from doctor.paper2.experiments.run_franka_closed_loop import (
    collect,
    validate_closed_loop_csv,
)


class _FakeClient:
    base_url = "http://fake/api/v1"

    def health_joints(self):
        return {"positions": [0.0]}

    def list_skills(self):
        return {"skills": ["go_to_tongue_pose", "go_to_face_pose"]}

    def go_to_skill(self, skill_name: str):
        return {"accepted": True, "skill_name": skill_name}


def _write_csv(path: Path, row: dict[str, str]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
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
        ]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerow(row)


def test_collect_records_successful_skill_calls():
    rows = collect(client=_FakeClient(), trials=2, skill_names=["go_to_tongue_pose"])  # type: ignore[arg-type]

    assert len(rows) == 2
    assert rows[0]["probe_status"] == "online"
    assert rows[0]["skill_success"] is True
    assert rows[0]["latency_ms"] >= 0.0


def test_validate_closed_loop_csv_accepts_online_success(tmp_path: Path):
    path = tmp_path / "franka_closed_loop.csv"
    _write_csv(
        path,
        {
            "trial_id": "franka_0000",
            "base_url": "http://fake/api/v1",
            "probe_status": "online",
            "skill_name": "go_to_tongue_pose",
            "skill_success": "True",
            "latency_ms": "12.5",
            "joints_ok": "True",
            "skills_ok": "True",
            "error": "",
        },
    )

    validation = validate_closed_loop_csv(path)
    assert validation.ready
    assert validation.successes == 1


def test_validate_closed_loop_csv_rejects_offline_probe(tmp_path: Path):
    path = tmp_path / "franka_closed_loop.csv"
    _write_csv(
        path,
        {
            "trial_id": "franka_0000",
            "base_url": "http://fake/api/v1",
            "probe_status": "offline",
            "skill_name": "go_to_tongue_pose",
            "skill_success": "False",
            "latency_ms": "0.0",
            "joints_ok": "False",
            "skills_ok": "False",
            "error": "offline",
        },
    )

    validation = validate_closed_loop_csv(path)
    assert not validation.ready
    assert "probe_status" in validation.reason
