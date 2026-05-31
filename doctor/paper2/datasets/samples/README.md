# Paper II Dataset Samples

This directory contains reviewable no-PHI fixtures for the dataset replay
pipeline. The rows are synthetic and use the same normalized case schema as the
in-code cases:

- `case_id`
- `symptom_text`
- `expected_entities`
- `vision_tags`
- `q_img`
- `conflict_label`
- `conflict_type`
- `fhir_missing`

List fields use `|` separators in CSV. Public or controlled datasets must be
converted into this derived schema outside the repository, with access and
license metadata recorded in `doctor/paper2/datasets/registry.json`.
