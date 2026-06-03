# Paper I — 离线主实验复现

## 环境

```bash
export PAPER1_ROOT="$(pwd)"   # doctor/paper1
python3 -m pip install -r requirements-paper1.txt
```

## 数据（ShezhenV3 全量）

```bash
bash ../../scripts/paper1_run_tcm_full.sh
```

或分步（与主表 Table II 一致）：

```bash
python3 scripts/import_shezhenv3.py
python3 experiments/edge_iqa/calibrate_tau_tcm.py    # -> recommended_tau.json (tau_B2)
python3 experiments/edge_iqa/calibrate_tau_b3.py     # -> recommended_tau_b3.json
python3 experiments/edge_iqa/roi_ablation.py
python3 experiments/run_matrix_tcm.py                  # -> main_seed*.csv, table_ii.json
python3 figures/plot_main.py
python3 experiments/reports/build_table_ii.py
python3 experiments/reports/build_table_iii.py
python3 experiments/reports/build_dataset_tables.py
```

## τ 消融 Fig.7

```bash
python3 experiments/run_ablation_tau.py
python3 figures/plot_ablation_tau.py
```

## M5 跨集报告

```bash
python3 experiments/cross_dataset_report.py
```

## 文稿 PDF

```bash
bash ../../scripts/paper1_build_draft.sh
```

预期产物：

- `experiments/results/recommended_tau.json`（主矩阵 $\tau_{B2}$，当前 ROI 标定 0.465）
- `experiments/results/main_seed{0,1,2}.csv`、`table_ii.json`
- `latex/sections/table_ii.tex`（由 `build_table_ii.py` 生成，勿手改数字）
- `figures/fig5_rtt_cdf.pdf`, `fig6_valid_rate.pdf`, `fig7_ablation_tau.pdf`
- `latex/main.pdf`, `latex/main-zh.pdf`

**勿将** `franka_m6_rtt.csv` 并入 Table II。

## 无 TCM 全量时的合成路径（legacy）

```bash
python3 scripts/synth_degrade.py
python3 experiments/edge_iqa/calibrate_tau.py
python3 experiments/run_matrix.py --config experiments/configs/main_exp.yaml
```

该路径与 ShezhenV3 主表数字无关，仅用于早期合成验证。
