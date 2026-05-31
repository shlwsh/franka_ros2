from doctor.paper2.tools.franka_client import FrankaApiClient


def test_client_normalizes_base_url():
    client = FrankaApiClient(base_url="http://127.0.0.1:8000/api/v1/")
    assert client.base_url == "http://127.0.0.1:8000/api/v1"
