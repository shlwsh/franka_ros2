# Graphical Abstract (layout spec)

**Title strip:** Confidence-Aware Edge Routing for Robotic TCM Tongue Imaging

**Left panel — Cloud–edge–device**
- FR3 arm + wrist camera (icon)
- Edge gateway box: `Edge-IQA` → `LangGraph router`
- Cloud icon: diagnosis / storage (dashed, optional)

**Center panel — Routing decision**
- Flowchart: score frame → if $Q_{img} \geq \tau_{B2}$ → upload; else resample (≤K) or fail-safe
- Highlight $\tau_{B2}=0.465$ on ROI crop

**Right panel — Key numbers (from Table II)**
- M1 p50: 374 ms → **208 ms** (B0→B2)
- M2: 0.560 → **0.604**
- Footnote: ShezhenV3 test, 3 seeds, physical resample

**Bottom strip**
- Dual-track: offline matrix (primary) + Franka JSONL (auxiliary)

> Export as `graphical_abstract.pdf` (single column, 1200×600 px recommended) when preparing the submission portal upload.
