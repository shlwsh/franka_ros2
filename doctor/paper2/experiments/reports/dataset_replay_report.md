# Dataset Replay Report

- dataset: sample_open_csv
- source: /home/ros/work/paper2/doctor/paper2/datasets/registry.json
- unique cases: 6
- replay rows: 120
- access levels: open
- licenses: project-local synthetic data; no PHI

| Baseline | Cases | F1 | Hallucination Rate | FHIR Valid Rate | Tool Call Rate |
|---|---:|---:|---:|---:|---:|
| B0 | 24 | 0.8000 | 0.5000 | 0.8333 | 0.0000 |
| B1 | 24 | 1.0000 | 0.1667 | 0.5000 | 0.1667 |
| B2 | 24 | 1.0000 | 0.0000 | 0.3333 | 0.3333 |
| B3 | 24 | 1.0000 | 0.1667 | 0.5000 | 0.5000 |
| B4 | 24 | 1.0000 | 0.1667 | 0.6667 | 0.5000 |
