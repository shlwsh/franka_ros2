import httpx
import os
import pytest  # noqa: F401 — used by skip
import subprocess
import time
from contextlib import closing
import socket

from conftest import find_free_port


@pytest.fixture(scope='module')
def paper1_api_url():
    port = find_free_port()
    host = '127.0.0.1'
    env = os.environ.copy()
    env['FRANKA_API_HOST'] = host
    env['FRANKA_API_PORT'] = str(port)
    env['FRANKA_API_AUTH_ENABLED'] = 'true'
    env['FRANKA_API_KEY'] = 'test-secret-key'
    env['PAPER1_MODE'] = '1'

    import sys

    process = subprocess.Popen(
        [
            sys.executable,
            '-m',
            'uvicorn',
            'franka_api_server.app:app',
            '--host',
            host,
            '--port',
            str(port),
        ],
        env=env,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    url = f'http://{host}:{port}'
    for _ in range(30):
        try:
            with socket.create_connection((host, port), timeout=1.0):
                break
        except OSError:
            time.sleep(0.5)
    else:
        process.terminate()
        _, err = process.communicate()
        raise RuntimeError(err.decode())

    yield url
    process.terminate()
    process.wait()


def test_paper1_mode_disables_controller_routes(paper1_api_url):
    client = httpx.Client(
        base_url=paper1_api_url,
        headers={'X-API-Key': 'test-secret-key'},
    )
    response = client.get('/api/v1/controller/list')
    assert response.status_code == 404
    client.close()


def test_paper1_mode_vision_and_skills(paper1_api_url):
    client = httpx.Client(
        base_url=paper1_api_url,
        headers={'X-API-Key': 'test-secret-key'},
    )
    skills = client.get('/api/v1/motion/skills')
    assert skills.status_code == 200

    from test_vision import SYNTH_CLEAR

    if not SYNTH_CLEAR.is_file():
        pytest.skip('synthetic data missing')
    vision = client.post(
        '/api/v1/vision/evaluate',
        files={'file': ('t.png', SYNTH_CLEAR.read_bytes(), 'image/png')},
    )
    assert vision.status_code == 200
    assert vision.json()['meta']['scorer'] == 'edge_iqa'
    client.close()
