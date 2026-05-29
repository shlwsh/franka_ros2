import subprocess
import sys
from pathlib import Path

import pytest

PAPER1_ROOT = Path(__file__).resolve().parents[2] / 'doctor' / 'paper1'
SYNTH_CLEAR = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear' / 'clear_0000.png'


@pytest.fixture(scope='module')
def sample_png_bytes() -> bytes:
    if not SYNTH_CLEAR.is_file():
        subprocess.run(
            [sys.executable, str(PAPER1_ROOT / 'scripts' / 'synth_degrade.py')],
            check=True,
            cwd=str(PAPER1_ROOT),
        )
    return SYNTH_CLEAR.read_bytes()


def test_vision_evaluate_multipart(api_client, sample_png_bytes):
    response = api_client.post(
        '/api/v1/vision/evaluate',
        files={'file': ('test.png', sample_png_bytes, 'image/png')},
    )
    assert response.status_code == 200
    data = response.json()
    assert 'q_img' in data
    assert isinstance(data['flags'], list)
    assert data['t_iqa_ms'] >= 0
    assert data['meta']['scorer'] == 'edge_iqa'


def test_vision_evaluate_requires_input(api_client):
    response = api_client.post('/api/v1/vision/evaluate', json={})
    assert response.status_code == 400


def test_vision_evaluate_synthetic_image(api_client):
    if not SYNTH_CLEAR.is_file():
        pytest.skip('synthetic data missing')
    response = api_client.post(
        '/api/v1/vision/evaluate',
        json={'image_path': str(SYNTH_CLEAR)},
    )
    assert response.status_code == 200
    data = response.json()
    assert data['meta']['scorer'] == 'edge_iqa'
    assert data['q_img'] > 0.4
