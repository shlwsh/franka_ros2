from doctor.paper2.tools.franka_client import FrankaApiError
from doctor.paper2.tools.franka_probe import probe


class _FakeClient:
    base_url = "http://fake/api/v1"

    def health_joints(self):
        return {"positions": []}

    def list_skills(self):
        return {"skills": ["go_to_tongue_pose"]}


class _OfflineClient:
    base_url = "http://offline/api/v1"

    def health_joints(self):
        raise FrankaApiError("offline")

    def list_skills(self):
        raise FrankaApiError("offline")


def test_probe_online_client():
    result = probe(_FakeClient())  # type: ignore[arg-type]
    assert result["status"] == "online"
    assert result["skills"] == ["go_to_tongue_pose"]


def test_probe_offline_client():
    result = probe(_OfflineClient())  # type: ignore[arg-type]
    assert result["status"] == "offline"
    assert len(result["errors"]) == 2
