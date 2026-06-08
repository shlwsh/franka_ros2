# Paper II Closed-Loop Summary Report

- latency source: /home/ros/work/paper2/doctor/paper2/experiments/results/closed_loop_latency.csv
- route source: /home/ros/work/paper2/doctor/paper2/experiments/logs/paper2_run_001.jsonl
- summary rows: 6

| Baseline | Trials | Mean ms | P50 ms | P95 ms | Tool Call Rate | Final Route Distribution |
|---|---:|---:|---:|---:|---:|---|
| ALL | 120 | 0.0478 | 0.0420 | 0.0785 | 0.3500 | ask_followup=9/120:0.0750;generate_emr=78/120:0.6500;human_review=27/120:0.2250;resample_vision=6/120:0.0500 |
| B0 | 24 | 0.0548 | 0.0430 | 0.1196 | 0.0000 | generate_emr=24/24:1.0000 |
| B1 | 24 | 0.0437 | 0.0420 | 0.0583 | 0.1250 | ask_followup=3/24:0.1250;generate_emr=15/24:0.6250;resample_vision=6/24:0.2500 |
| B2 | 24 | 0.0433 | 0.0395 | 0.0577 | 0.3750 | ask_followup=3/24:0.1250;generate_emr=9/24:0.3750;human_review=12/24:0.5000 |
| B3 | 24 | 0.0499 | 0.0440 | 0.0717 | 0.6250 | ask_followup=3/24:0.1250;generate_emr=15/24:0.6250;human_review=6/24:0.2500 |
| B4 | 24 | 0.0471 | 0.0415 | 0.0679 | 0.6250 | generate_emr=15/24:0.6250;human_review=9/24:0.3750 |
