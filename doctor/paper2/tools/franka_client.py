"""HTTP client for the existing franka_api_server tool surface.

The client intentionally uses the Python standard library so Paper II synthetic
experiments remain dependency-light. Network calls are optional; the MVP runner
uses synthetic tools unless a later integration script explicitly instantiates
this client.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

DEFAULT_BASE_URL = os.getenv("FRANKA_API_BASE", "http://127.0.0.1:8000/api/v1")
DEFAULT_API_KEY = os.getenv("FRANKA_API_KEY", "franka-api-default-key")


class FrankaApiError(RuntimeError):
    """Raised when franka_api_server returns an error or cannot be reached."""


class FrankaApiClient:
    def __init__(
        self,
        base_url: str = DEFAULT_BASE_URL,
        api_key: str = DEFAULT_API_KEY,
        timeout_s: float = 30.0,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout_s = timeout_s

    def _request(
        self,
        method: str,
        path: str,
        *,
        body: bytes | None = None,
        content_type: str = "application/json",
    ) -> dict[str, Any]:
        req = urllib.request.Request(
            f"{self.base_url}{path}",
            data=body,
            method=method,
            headers={"X-API-Key": self.api_key, "Content-Type": content_type},
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout_s) as response:
                payload = response.read().decode("utf-8")
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            raise FrankaApiError(str(exc)) from exc
        return json.loads(payload) if payload else {}

    def health_joints(self) -> dict[str, Any]:
        return self._request("GET", "/status/joints")

    def list_skills(self) -> dict[str, Any]:
        return self._request("GET", "/motion/skills")

    def go_to_skill(self, skill_name: str) -> dict[str, Any]:
        return self._request("POST", f"/motion/skills/{skill_name}")

    def evaluate_image_path(self, image_path: Path) -> dict[str, Any]:
        body = json.dumps({"image_path": str(image_path.resolve())}).encode("utf-8")
        return self._request("POST", "/vision/evaluate", body=body)
