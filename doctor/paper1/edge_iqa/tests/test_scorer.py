"""Tests for edge_iqa.scorer using synthetic images."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

PAPER1_ROOT = Path(__file__).resolve().parents[2]
SYNTH_CLEAR = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
SYNTH_BLUR = PAPER1_ROOT / 'experiments' / 'synthetic' / 'blur'


@pytest.fixture(scope='module', autouse=True)
def ensure_synthetic():
    if not (SYNTH_CLEAR / 'clear_0000.png').is_file():
        subprocess.run(
            [sys.executable, str(PAPER1_ROOT / 'scripts' / 'synth_degrade.py')],
            check=True,
            cwd=str(PAPER1_ROOT),
        )


def test_clear_vs_blur_separation():
    from edge_iqa.scorer import compute_q

    clear_scores = []
    blur_scores = []
    for i in range(10):
        clear_scores.append(compute_q(SYNTH_CLEAR / f'clear_{i:04d}.png').q_img)
        blur_scores.append(compute_q(SYNTH_BLUR / f'blur_{i:04d}.png').q_img)

    mean_clear = sum(clear_scores) / len(clear_scores)
    mean_blur = sum(blur_scores) / len(blur_scores)
    assert mean_clear - mean_blur > 0.2, f'clear={mean_clear:.3f} blur={mean_blur:.3f}'


def test_blur_flag():
    from edge_iqa.scorer import compute_q

    r = compute_q(SYNTH_BLUR / 'blur_0000.png')
    assert 'blur' in r.flags


def test_cli_json():
    img = SYNTH_CLEAR / 'clear_0000.png'
    proc = subprocess.run(
        [sys.executable, '-m', 'edge_iqa.cli', '--image', str(img), '--json'],
        cwd=str(PAPER1_ROOT),
        capture_output=True,
        text=True,
        check=True,
    )
    assert '"q_img"' in proc.stdout
