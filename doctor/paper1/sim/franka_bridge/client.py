"""HTTP client for franka_api_server (Paper I phase 1 stub)."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import httpx

DEFAULT_BASE = os.getenv('FRANKA_API_BASE', 'http://127.0.0.1:8000/api/v1')
DEFAULT_KEY = os.getenv('FRANKA_API_KEY', 'franka-api-default-key')


class FrankaApiClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE,
        api_key: str = DEFAULT_KEY,
        timeout_s: float = 30.0,
    ):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self._client = httpx.Client(
            base_url=self.base_url,
            headers={'X-API-Key': api_key},
            timeout=timeout_s,
        )

    def health_joints(self) -> Dict[str, Any]:
        r = self._client.get('/status/joints')
        r.raise_for_status()
        return r.json()

    def evaluate_image(self, image_path: Path) -> Dict[str, Any]:
        path = Path(image_path)
        if path.is_file():
            with path.open('rb') as f:
                r = self._client.post(
                    '/vision/evaluate',
                    files={'file': (path.name, f, 'image/png')},
                )
        else:
            r = self._client.post(
                '/vision/evaluate',
                json={'image_path': str(path.resolve())},
            )
        r.raise_for_status()
        return r.json()

    def go_to_skill(self, skill_name: str) -> Dict[str, Any]:
        r = self._client.post(f'/motion/skills/{skill_name}')
        r.raise_for_status()
        return r.json()

    def list_skills(self) -> Dict[str, Any]:
        r = self._client.get('/motion/skills')
        r.raise_for_status()
        return r.json()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> 'FrankaApiClient':
        return self

    def __exit__(self, *args: object) -> None:
        self.close()
