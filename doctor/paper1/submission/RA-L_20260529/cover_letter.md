# Cover Letter (Draft) — RA-L / RCIM

**Date:** 2026-06-04  
**Manuscript:** *Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging: Edge-IQA and LangGraph Closed-Loop Acquisition*  
**Authors:** Honglei Shi, Juanjuan Zhao (石洪雷, 赵涓涓)  
**Affiliation:** Taiyuan University of Technology (太原理工大学)  
**Corresponding author:** Honglei Shi (石洪雷), Taiyuan University of Technology  
**Email:** shihonglei0042@link.tyut.edu.cn

---

Dear Editor,

We submit the enclosed manuscript for consideration as a **Regular Paper** in IEEE Robotics and Automation Letters (or, alternatively, Robotics and Computer-Integrated Manufacturing). The work addresses **acquisition-time quality gating** for robotic traditional Chinese medicine (TCM) tongue imaging under cloud--edge--device collaboration.

## Summary

Tele-diagnosis pipelines often upload every camera frame to the cloud, wasting bandwidth on blurred or poorly exposed tongue images and inflating round-trip latency (RTT). We keep a lightweight **Edge-IQA** scorer and a **LangGraph** confidence-aware router on the edge gateway, outside the 1\,kHz ROS~2 control loop, and validate the stack on the public **ShezhenV3-COCO** corpus (6{,}719 images) plus an auxiliary **Franka** execution track.

## Contributions

1. **Edge-IQA with COCO tongue ROI** — $O(HW)$ CPU scoring with interpretable blur/exposure flags; $\tau_{B2}{=}0.465$ calibrated on 572 validation pairs (p95 $\approx$ 9.6\,ms at 512\,px).
2. **Auditable three-branch routing** — upload / edge resample / fail-safe under retry budget $K{=}2$, logged as JSONL for reproduction.
3. **Dual-track evaluation** — offline primary matrix on 553 test images (500 frames $\times$ 3 seeds) and separate M6 Franka trials that do not alter Table~II statistics.

## Key results (Table II, script-generated)

| Metric | B0 (naive upload) | B2 (proposed) |
|--------|-------------------|---------------|
| M1 RTT p50 | 374.0 ms | **208.3 ms** |
| M2 valid-frame rate | 0.560 | **0.604** |

Learned MobileNet baselines B3/B4 reach M2 $\approx 0.93$ at recalibrated thresholds with higher edge RTT; we report them honestly as comparators, not as the primary deployable path.
A Pareto plot (M2 vs.\ M1 p50) and appendix rows for BRISQUE / NIQE-style scorers under the same LangGraph shell further clarify the valid-rate vs.\ latency trade-off.

## Reproducibility and ethics

Splits, calibration JSON, and one-command reproduction (`scripts/paper1_run_tcm_full.sh`, `REPRODUCE.md`) ship in `doctor/paper1/`.
Extended tables, NR-IQA baselines, stratified M2, deployment notes, and the B2 walkthrough are in `doctor/paper1/supplementary/SUPPLEMENTARY.md` (RA-L does not permit appendices beyond the 8-page PDF limit).
ShezhenV3 images remain at the user-configured dataset root. Offline experiments use a public corpus; no new human subjects were recruited; JSONL logs contain no patient identifiers. Generative AI assisted prose and documentation only; all metrics were verified against `experiments/results/*.json`.

## Suitability for RA-L

The paper couples **robotic acquisition**, **edge inference**, and **closed-loop policies** with hardware-in-the-loop feasibility on FR3, while keeping the primary evidence chain offline and auditable—aligned with RA-L's emphasis on rigorous robotics systems contributions.

## Declarations

- The manuscript is original and not under consideration elsewhere.
- All authors have approved the submission.
- **Conflict of interest:** none declared.
- **Suggested reviewers:** [optional list]

Sincerely,  

Honglei Shi (石洪雷)  
Taiyuan University of Technology (太原理工大学)  
E-mail: shihonglei0042@link.tyut.edu.cn
