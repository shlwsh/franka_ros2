from doctor.paper2.agents.emr_fhir_agent import build_fhir_bundle
from doctor.paper2.tools.fhir_validator import validate_bundle, validate_external, validate_local


def _draft():
    return {"case_id": "case_validator", "assessment": "Synthetic assessment"}


def test_local_validator_accepts_valid_bundle():
    result = validate_local(build_fhir_bundle(_draft()))
    assert result.valid
    assert result.mode == "local-structural"


def test_local_validator_rejects_invalid_bundle():
    result = validate_bundle({"resourceType": "Bundle", "type": "collection", "entry": []})
    assert not result.valid
    assert "bundle.type must be document" in result.errors


def test_external_validator_failure_falls_back_to_error():
    result = validate_external(build_fhir_bundle(_draft()), "definitely_missing_validator {path}")
    assert not result.valid
    assert result.mode == "external"
    assert result.errors
