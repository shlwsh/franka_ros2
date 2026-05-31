# Dataset Compliance Audit Report

Preflight audit for Paper II dataset registry and derived no-PHI case files.

- datasets: 4
- ready: 2
- partial: 0
- blocked: 2
- required datasets ready: 0/2
- submission-dataset-ready: no
- phi flags: 0

| Dataset | Status | Required | Cases | PHI Flags | Reason | Next Action |
|---|---|---:|---:|---:|---|---|
| mimic_cxr_placeholder | blocked | yes | 0 | 0 | controlled dataset has no local derived file path | derive no-PHI cases outside the repo and add local_path after approval |
| mimic_iv_note_placeholder | blocked | yes | 0 | 0 | controlled dataset has no local derived file path | derive no-PHI cases outside the repo and add local_path after approval |
| sample_open_csv | ready | no | 6 | 0 | dataset metadata and derived cases passed the preflight audit | run dataset replay or keep as a software fixture |
| synthetic_builtin | ready | no | 8 | 0 | dataset metadata and derived cases passed the preflight audit | run dataset replay or keep as a software fixture |
