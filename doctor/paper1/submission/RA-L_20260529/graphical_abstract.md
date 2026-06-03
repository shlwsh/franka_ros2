# Graphical Abstract (RA-L optional) — Paper I

**Title:** Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging

## Layout (single panel, landscape)

```
[ FR3 arm + camera ] --> [ Edge gateway box ]
                              |
                    Edge-IQA (Q_img, flags)
                              |
                    LangGraph router
                     /      |      \
            upload_cloud  resample_edge  fail_safe
                              |
                    [ Cloud TCM analytics ]
```

## Key numbers (Table II, simulated RTT)

| | B0 | B2 |
|---|-----|-----|
| M1 p50 | 374 ms | **208 ms** |
| M2 | 0.560 | **0.604** |

## Caption (≤ 80 words)

Robotic tongue imaging for TCM tele-diagnosis couples FR3 acquisition with edge-side Edge-IQA and LangGraph routing.
Low-quality frames are filtered or re-captured before cloud upload, cutting median RTT under a documented latency model while improving valid-frame rate on ShezhenV3-COCO.

## Asset

For submission, export `figures/fig1_system_overview.svg` or compose a 1200×600 PNG from Fig.1 + Pareto inset (`fig7_pareto_m2_m1.pdf`).
