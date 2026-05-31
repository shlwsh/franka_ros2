"""Paper II case loading utilities.

The built-in cases are deliberately small and transparent. They exercise the
routing logic without requiring clinical data, restricted ontologies, or LLM
calls. The file loader adds a license-aware bridge for later public or
controlled dataset replay while keeping the default synthetic behavior intact.
"""

from __future__ import annotations

import csv
import json
from copy import deepcopy
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_REGISTRY_PATH = ROOT / "datasets" / "registry.json"
REQUIRED_CASE_FIELDS = {
    "case_id",
    "symptom_text",
    "expected_entities",
    "vision_tags",
    "q_img",
    "conflict_label",
}
CONTROLLED_ACCESS_LEVELS = {"controlled", "restricted"}


_CASES: list[dict[str, Any]] = [
    {
        "case_id": "case_clear_fever",
        "symptom_text": "Patient reports fever and sore throat for two days.",
        "expected_entities": ["fever", "sore_throat"],
        "vision_tags": ["red_tongue"],
        "q_img": 0.88,
        "conflict_label": False,
        "conflict_type": "none",
        "fhir_missing": False,
    },
    {
        "case_id": "case_blur_fever",
        "symptom_text": "Patient reports fever and sore throat for two days.",
        "expected_entities": ["fever", "sore_throat"],
        "vision_tags": ["red_tongue"],
        "q_img": 0.39,
        "conflict_label": True,
        "conflict_type": "vision_low_quality",
        "fhir_missing": False,
    },
    {
        "case_id": "case_cold_pale",
        "symptom_text": "Patient reports cold aversion and fatigue.",
        "expected_entities": ["cold_aversion", "fatigue"],
        "vision_tags": ["pale_tongue", "thin_white_coating"],
        "q_img": 0.81,
        "conflict_label": False,
        "conflict_type": "none",
        "fhir_missing": False,
    },
    {
        "case_id": "case_cold_yellow_conflict",
        "symptom_text": "Patient reports cold aversion and fatigue.",
        "expected_entities": ["cold_aversion", "fatigue"],
        "vision_tags": ["yellow_greasy_coating"],
        "q_img": 0.84,
        "conflict_label": True,
        "conflict_type": "text_vision_contradiction",
        "fhir_missing": False,
    },
    {
        "case_id": "case_missing_text",
        "symptom_text": "Patient reports feeling unwell for several days.",
        "expected_entities": ["fever"],
        "vision_tags": ["red_tongue"],
        "q_img": 0.77,
        "conflict_label": True,
        "conflict_type": "text_missing_entity",
        "fhir_missing": False,
    },
    {
        "case_id": "case_mouth_bitter",
        "symptom_text": "Patient reports mouth bitter and nausea after meals.",
        "expected_entities": ["mouth_bitter", "nausea"],
        "vision_tags": ["yellow_greasy_coating"],
        "q_img": 0.79,
        "conflict_label": False,
        "conflict_type": "none",
        "fhir_missing": True,
    },
    {
        "case_id": "case_mouth_bitter_white_conflict",
        "symptom_text": "Patient reports mouth bitter and nausea after meals.",
        "expected_entities": ["mouth_bitter", "nausea"],
        "vision_tags": ["thin_white_coating"],
        "q_img": 0.76,
        "conflict_label": True,
        "conflict_type": "text_vision_contradiction",
        "fhir_missing": False,
    },
    {
        "case_id": "case_occluded_cold",
        "symptom_text": "Patient reports cold aversion and fatigue.",
        "expected_entities": ["cold_aversion", "fatigue"],
        "vision_tags": ["pale_tongue"],
        "q_img": 0.46,
        "conflict_label": True,
        "conflict_type": "vision_low_quality",
        "fhir_missing": True,
    },
]


def load_dataset_registry(path: Path = DEFAULT_REGISTRY_PATH) -> dict[str, dict[str, Any]]:
    if not path.is_file():
        return {}
    payload = json.loads(path.read_text(encoding="utf-8"))
    datasets = payload.get("datasets", [])
    registry: dict[str, dict[str, Any]] = {}
    for item in datasets:
        dataset_id = str(item.get("dataset_id", "")).strip()
        if dataset_id:
            registry[dataset_id] = dict(item)
    return registry


def _parse_list(value: Any, *, field: str, source: str) -> list[str]:
    if value is None:
        return []
    if isinstance(value, (list, tuple, set)):
        return [str(item).strip() for item in value if str(item).strip()]
    text = str(value).strip()
    if not text:
        return []
    if text.startswith("["):
        try:
            parsed = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{source}: {field} is not valid JSON list") from exc
        if not isinstance(parsed, list):
            raise ValueError(f"{source}: {field} must be a list")
        return [str(item).strip() for item in parsed if str(item).strip()]
    separator = ";" if ";" in text else "|"
    if separator in text:
        return [item.strip() for item in text.split(separator) if item.strip()]
    return [text]


def _parse_bool(value: Any, *, field: str, source: str) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return bool(value)
    text = str(value).strip().lower()
    if text in {"", "false", "0", "no", "n"}:
        return False
    if text in {"true", "1", "yes", "y"}:
        return True
    raise ValueError(f"{source}: {field} must be boolean-like")


def _normalize_case(raw: dict[str, Any], *, source: str) -> dict[str, Any]:
    missing = [
        field
        for field in sorted(REQUIRED_CASE_FIELDS)
        if field not in raw or raw[field] is None or str(raw[field]).strip() == ""
    ]
    if missing:
        raise ValueError(f"{source}: missing required field(s): {', '.join(missing)}")

    try:
        q_img = float(raw["q_img"])
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{source}: q_img must be numeric") from exc
    if q_img < 0.0 or q_img > 1.0:
        raise ValueError(f"{source}: q_img must be in [0, 1]")

    case = dict(raw)
    case.update(
        {
            "case_id": str(raw["case_id"]).strip(),
            "symptom_text": str(raw["symptom_text"]).strip(),
            "expected_entities": _parse_list(
                raw["expected_entities"], field="expected_entities", source=source
            ),
            "vision_tags": _parse_list(raw["vision_tags"], field="vision_tags", source=source),
            "q_img": round(q_img, 4),
            "conflict_label": _parse_bool(
                raw["conflict_label"], field="conflict_label", source=source
            ),
            "conflict_type": str(raw.get("conflict_type") or "none").strip(),
            "fhir_missing": _parse_bool(
                raw.get("fhir_missing", False), field="fhir_missing", source=source
            ),
        }
    )
    return case


def _load_csv(path: Path) -> list[dict[str, Any]]:
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            _normalize_case(dict(row), source=f"{path}:{idx}")
            for idx, row in enumerate(reader, start=2)
        ]


def _load_jsonl(path: Path) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    with path.open(encoding="utf-8") as f:
        for idx, line in enumerate(f, start=1):
            if not line.strip():
                continue
            payload = json.loads(line)
            if not isinstance(payload, dict):
                raise ValueError(f"{path}:{idx}: JSONL row must be an object")
            cases.append(_normalize_case(payload, source=f"{path}:{idx}"))
    return cases


def _load_json(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    rows = payload.get("cases", payload) if isinstance(payload, dict) else payload
    if not isinstance(rows, list):
        raise ValueError(f"{path}: JSON dataset must be a list or contain a cases list")
    cases: list[dict[str, Any]] = []
    for idx, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise ValueError(f"{path}:{idx}: JSON case must be an object")
        cases.append(_normalize_case(row, source=f"{path}:{idx}"))
    return cases


def load_cases_from_file(path: Path | str) -> list[dict[str, Any]]:
    source_path = Path(path)
    if not source_path.is_file():
        raise FileNotFoundError(f"dataset file not found: {source_path}")
    suffix = source_path.suffix.lower()
    if suffix == ".csv":
        cases = _load_csv(source_path)
    elif suffix == ".jsonl":
        cases = _load_jsonl(source_path)
    elif suffix == ".json":
        cases = _load_json(source_path)
    else:
        raise ValueError(f"unsupported dataset format: {source_path.suffix}")
    if not cases:
        raise ValueError(f"dataset has no cases: {source_path}")
    return cases


def _validate_dataset_record(record: dict[str, Any], *, allow_controlled: bool) -> None:
    dataset_id = str(record.get("dataset_id", "")).strip()
    for field in ("dataset_id", "access_level", "license", "source_type"):
        if not str(record.get(field, "")).strip():
            raise ValueError(f"dataset registry entry {dataset_id or '<unknown>'} missing {field}")
    access_level = str(record.get("access_level", "")).strip().lower()
    if access_level in CONTROLLED_ACCESS_LEVELS and not allow_controlled:
        raise PermissionError(
            f"dataset '{dataset_id}' is {access_level}; pass allow_controlled=True only "
            "after credentialing, local data-use approval, and de-identification checks"
        )


def _resolve_dataset_path(record: dict[str, Any], registry_path: Path) -> Path:
    raw_path = record.get("path") or record.get("local_path")
    dataset_id = str(record.get("dataset_id", "")).strip()
    if not raw_path:
        raise FileNotFoundError(
            f"dataset '{dataset_id}' has no local path; it is a registry placeholder only"
        )
    path = Path(str(raw_path))
    if not path.is_absolute():
        path = registry_path.parent / path
    return path


def _attach_dataset_metadata(cases: list[dict[str, Any]], record: dict[str, Any]) -> list[dict[str, Any]]:
    metadata = {
        "dataset_id": record["dataset_id"],
        "dataset_access_level": record["access_level"],
        "dataset_license": record["license"],
    }
    return [{**case, **metadata} for case in cases]


def load_cases(
    source: Path | str | None = None,
    *,
    dataset_id: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    allow_controlled: bool = False,
) -> list[dict[str, Any]]:
    if source is None and dataset_id is None:
        return deepcopy(_CASES)

    if dataset_id:
        registry = load_dataset_registry(registry_path)
        if dataset_id not in registry:
            raise KeyError(f"dataset_id not found in registry: {dataset_id}")
        record = registry[dataset_id]
        _validate_dataset_record(record, allow_controlled=allow_controlled)
        if record.get("source_type") == "builtin_synthetic":
            return _attach_dataset_metadata(deepcopy(_CASES), record)
        source = _resolve_dataset_path(record, registry_path)
        return _attach_dataset_metadata(load_cases_from_file(source), record)

    if source is None:
        raise ValueError("source or dataset_id is required")
    return load_cases_from_file(source)


def expand_loaded_cases(cases: list[dict[str, Any]], trials: int) -> list[dict[str, Any]]:
    if trials < 1:
        raise ValueError("trials must be >= 1")
    if not cases:
        raise ValueError("cases must not be empty")
    expanded: list[dict[str, Any]] = []
    for idx in range(trials):
        case = deepcopy(cases[idx % len(cases)])
        case["trial_index"] = idx
        expanded.append(case)
    return expanded


def expand_cases(
    trials: int,
    source: Path | str | None = None,
    *,
    dataset_id: str | None = None,
    registry_path: Path = DEFAULT_REGISTRY_PATH,
    allow_controlled: bool = False,
) -> list[dict[str, Any]]:
    cases = load_cases(
        source=source,
        dataset_id=dataset_id,
        registry_path=registry_path,
        allow_controlled=allow_controlled,
    )
    return expand_loaded_cases(cases, trials)
