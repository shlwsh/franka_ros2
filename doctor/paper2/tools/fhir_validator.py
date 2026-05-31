"""FHIR validator adapter for Paper II.

The MVP always has a deterministic local validator. If a real validator command
is available, set `PAPER2_FHIR_VALIDATOR_CMD` to a command template that accepts
the JSON file path as `{path}`. Example:

    PAPER2_FHIR_VALIDATOR_CMD='java -jar validator_cli.jar {path} -version 4.0.1'

The adapter records the mode and raw output so paper results can distinguish
lightweight structural validation from an external FHIR validator.
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from doctor.paper2.agents.emr_fhir_agent import validate_fhir_bundle

DEFAULT_TIMEOUT_S = float(os.getenv("PAPER2_FHIR_VALIDATOR_TIMEOUT_S", "30"))


@dataclass(frozen=True)
class FhirValidationResult:
    valid: bool
    errors: list[str]
    mode: str
    stdout: str = ""
    stderr: str = ""


def validate_local(bundle: dict[str, Any]) -> FhirValidationResult:
    valid, errors = validate_fhir_bundle(bundle)
    return FhirValidationResult(valid=valid, errors=errors, mode="local-structural")


def validate_external(
    bundle: dict[str, Any],
    command_template: str,
    *,
    timeout_s: float = DEFAULT_TIMEOUT_S,
) -> FhirValidationResult:
    with tempfile.NamedTemporaryFile("w", suffix=".json", encoding="utf-8", delete=False) as f:
        json.dump(bundle, f, ensure_ascii=False, sort_keys=True)
        path = Path(f.name)
    try:
        cmd = shlex.split(command_template.format(path=str(path)))
        proc = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout_s,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        return FhirValidationResult(
            valid=False,
            errors=[f"external validator failed: {exc}"],
            mode="external",
            stderr=str(exc),
        )
    finally:
        try:
            path.unlink()
        except OSError:
            pass

    errors: list[str] = []
    output = f"{proc.stdout}\n{proc.stderr}".lower()
    if proc.returncode != 0:
        errors.append(f"external validator returncode={proc.returncode}")
    if "error" in output and "0 error" not in output and "0 errors" not in output:
        errors.append("external validator reported errors")
    return FhirValidationResult(
        valid=not errors,
        errors=errors,
        mode="external",
        stdout=proc.stdout,
        stderr=proc.stderr,
    )


def validate_bundle(
    bundle: dict[str, Any],
    *,
    command_template: str | None = None,
) -> FhirValidationResult:
    command_template = command_template or os.getenv("PAPER2_FHIR_VALIDATOR_CMD")
    if command_template:
        external = validate_external(bundle, command_template)
        if external.valid:
            return external
        local = validate_local(bundle)
        return FhirValidationResult(
            valid=False,
            errors=external.errors + [f"local:{error}" for error in local.errors],
            mode="external+local-fallback",
            stdout=external.stdout,
            stderr=external.stderr,
        )
    return validate_local(bundle)
