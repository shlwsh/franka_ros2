# Paper I — 离线主实验复现

## 环境

```bash
export PAPER1_ROOT="$(pwd)"   # doctor/paper1
python3 -m pip install -r requirements-paper1.txt
```

## 数据（无 TCM 全量时）

```bash
python3 scripts/synth_degrade.py
python3 experiments/edge_iqa/calibrate_tau.py
```

## 主实验 Table II / Fig.5–6

```bash
python3 experiments/run_matrix.py --config experiments/configs/main_exp.yaml
python3 figures/plot_main.py
python3 experiments/reports/build_table_ii.py
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
# 英文 + 中文（同目录）
bash ../../scripts/paper1_build_draft.sh
# 或仅中文：
cd latex && xelatex -interaction=nonstopmode main-zh.tex && bibtex main-zh && xelatex main-zh.tex && xelatex main-zh.tex
```

预期产物：

- `experiments/results/main_seed{0,1,2}.csv`
- `figures/fig5_rtt_cdf.pdf`, `fig6_valid_rate.pdf`, `fig7_ablation_tau.pdf`
- `latex/main.pdf`

**勿将** `franka_m6_rtt.csv` 并入 `main_exp.yaml` 或 Table II。
