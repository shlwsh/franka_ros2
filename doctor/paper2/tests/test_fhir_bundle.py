from doctor.paper2.agents.emr_fhir_agent import (
    build_fhir_bundle,
    repair_fhir_bundle,
    validate_fhir_bundle,
)


def _draft():
    return {
        "case_id": "case_test",
        "assessment": "Synthetic assessment",
        "symptom_entities": [],
        "vision_findings": [],
    }


def test_fhir_bundle_is_document_with_composition_first():
    bundle = build_fhir_bundle(_draft())
    assert bundle["type"] == "document"
    assert bundle["entry"][0]["resource"]["resourceType"] == "Composition"
    assert bundle["entry"][0]["resource"]["subject"]["reference"] == "Patient/synthetic-case_test"
    valid, errors = validate_fhir_bundle(bundle)
    assert valid, errors


def test_repair_adds_missing_observation():
    draft = _draft()
    bundle = build_fhir_bundle(draft, omit_observation=True)
    valid, errors = validate_fhir_bundle(bundle)
    assert not valid
    assert "missing Observation resource" in errors
    repaired = repair_fhir_bundle(bundle, draft)
    valid, errors = validate_fhir_bundle(repaired)
    assert valid, errors
