import json
from pathlib import Path

import pytest

from doctor.paper2.tools.dataset_loader import (
    DEFAULT_REGISTRY_PATH,
    expand_cases,
    load_cases,
    load_dataset_registry,
)


def test_load_registered_open_sample_csv():
    cases = load_cases(dataset_id="sample_open_csv")
    assert len(cases) == 6
    assert cases[0]["expected_entities"] == ["fever", "sore_throat"]
    assert cases[0]["vision_tags"] == ["red_tongue"]
    assert cases[0]["dataset_id"] == "sample_open_csv"
    assert cases[1]["conflict_label"] is True


def test_expand_cases_accepts_registered_dataset():
    cases = expand_cases(8, dataset_id="sample_open_csv")
    assert len(cases) == 8
    assert cases[0]["trial_index"] == 0
    assert cases[-1]["trial_index"] == 7
    assert cases[-1]["dataset_id"] == "sample_open_csv"


def test_controlled_dataset_placeholder_requires_explicit_approval():
    with pytest.raises(PermissionError):
        load_cases(dataset_id="mimic_iv_note_placeholder")


def test_registry_contains_license_metadata():
    registry = load_dataset_registry(DEFAULT_REGISTRY_PATH)
    assert registry["sample_open_csv"]["access_level"] == "open"
    assert "license" in registry["mimic_cxr_placeholder"]


def test_jsonl_case_loader_normalizes_lists_and_bools(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps(
            {
                "case_id": "jsonl_001",
                "symptom_text": "Patient reports fever.",
                "expected_entities": ["fever"],
                "vision_tags": ["red_tongue"],
                "q_img": "0.74",
                "conflict_label": "false",
                "conflict_type": "none",
                "fhir_missing": "true",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    cases = load_cases(source=path)
    assert cases == [
        {
            "case_id": "jsonl_001",
            "symptom_text": "Patient reports fever.",
            "expected_entities": ["fever"],
            "vision_tags": ["red_tongue"],
            "q_img": 0.74,
            "conflict_label": False,
            "conflict_type": "none",
            "fhir_missing": True,
        }
    ]


def test_invalid_case_rejects_out_of_range_quality(tmp_path: Path):
    path = tmp_path / "cases.jsonl"
    path.write_text(
        json.dumps(
            {
                "case_id": "bad",
                "symptom_text": "Patient reports fever.",
                "expected_entities": ["fever"],
                "vision_tags": ["red_tongue"],
                "q_img": 1.2,
                "conflict_label": False,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="q_img"):
        load_cases(source=path)
