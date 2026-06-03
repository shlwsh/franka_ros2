# Paper I — Online Worked Example (B2 Walkthrough)

> **Moved out of the print appendix** per review AP-008 (2026-06-03).  
> Content mirrors the former `05_11_walkthrough.tex`.  
> **Print manuscript**: cite as online supplementary; do not expect this in the PDF body.

## Scenario

Test image `test/images/A (42).jpg` (ShezhenV3 test split) with COCO box `[120, 80, 400, 320]`.

After ROI crop (8% padding) and 512px resize, Edge-IQA yields $S=0.48$, $E=0.62$, $Q_{img}=0.53$, no flags. With $\tau_{B2}=0.465$ the frame passes on the first attempt.

## Degraded twin

Gaussian blur $r=3.2$ gives $Q_{img}=0.38$, flag `blur`. LangGraph selects `resample_edge`; after **physical skill transforms** (not random Q uplift) a second score draw crosses $\tau$ within $K=2$ for many trials—consistent with aggregate B2 M2$=0.604$.

## Calibration context (negative separability)

On the full validation cohort, `separation_min_clear_max_blur = -0.541`: clear and blurred score ranges **overlap**. This walkthrough shows a single frame pair; aggregate routing utility is reported in Table II and stratified M2 (`table_stratified_m2.tex`).

## Latency stack (one resample then upload)

Capture 5ms + IQA 9ms + route 1.5ms + resample ~50ms + second IQA + route + cloud 200–400ms ⇒ RTT ~280–480ms.

Uses the **documented simulated latency model** (`sim/NETEM.md`); not a measured WAN trace.

## JSONL excerpt

```json
{"frame_id":17,"q_img":0.53,"flags":[],"route_decision":"upload_cloud","retry_count":0,"baseline":"B2","degraded":false}
{"frame_id":18,"q_img":0.41,"flags":["blur"],"route_decision":"resample_edge","retry_count":1,"baseline":"B2","degraded":true}
```

## Reproduce

```bash
bash scripts/paper1_run_tcm_full.sh
python3 experiments/run_matrix_tcm.py --baseline B2 --seed 0 --n-frames 20
```

## Related artifacts

| Item | Path |
|------|------|
| τ calibration | `experiments/results/recommended_tau.json` |
| Main matrix | `experiments/results/main_seed0_detail.csv` |
| Sample JSONL | `docs-zh/paper1/V19/samples/run_001.sample.jsonl` |
