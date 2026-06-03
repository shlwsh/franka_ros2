# Paper I — 离线主实验复现

> **数字汇总**：运行完成后执行 `python3 ../../scripts/paper1_summarize_full_run.py` → [`docs/验证结果_全量.md`](docs/验证结果_全量.md)  
> **更新**：2026-06-04

## 环境

```bash
export PAPER1_ROOT="$(pwd)"   # doctor/paper1
python3 -m pip install -r requirements-paper1.txt
# B3 训练 / 主矩阵需 PyTorch（见 .venv）
```

## 一键全量（推荐）

```bash
bash ../../scripts/paper1_run_tcm_full.sh
```

日志：`experiments/logs/tcm_full_run.log`

## 分步复现（与 Table II 一致）

```bash
python3 scripts/import_shezhenv3.py
python3 experiments/edge_iqa/train_b3_mobilenet.py          # 若 b3_mobilenet.pt 不存在
python3 experiments/edge_iqa/calibrate_tau_tcm.py         # -> recommended_tau.json (tau_B2, separation)
python3 experiments/edge_iqa/calibrate_tau_b3.py            # -> recommended_tau_b3.json
python3 experiments/edge_iqa/roi_ablation.py
python3 experiments/cross_dataset_report.py                 # M5 Spearman
python3 experiments/run_matrix_tcm.py                       # -> main_seed*.csv, table_ii.json
python3 experiments/run_ablation_tau.py                     # Fig.7 τ 消融
python3 figures/plot_iqa_hist.py                            # Fig.3 标定直方图
python3 figures/plot_main.py                                # Fig.4 RTT CDF, Fig.5 M2 柱图
python3 experiments/reports/build_table_ii.py               # Table II + bootstrap 表注
python3 experiments/reports/build_table_iii.py              # Table III (B3/B4)
python3 experiments/reports/build_dataset_tables.py
python3 experiments/reports/build_paper1_artifacts.py       # 分层 M2 + Pareto + bootstrap JSON
python3 experiments/reports/build_table_ii.py               # 再次运行以注入 bootstrap 表注
python3 experiments/reports/sync_table_ii_zh.py
python3 experiments/replay_nr_matrix.py                     # NR-IQA 附录矩阵
python3 experiments/reports/build_table_nr_iqa.py
bash ../../scripts/paper1_build_draft.sh                    # main.pdf + main-zh.pdf
```

## 改稿专用脚本（2026-06-03）

| 脚本 | 产物 |
|------|------|
| `experiments/reports/build_paper1_artifacts.py` | `table_ii_bootstrap.json`、`table_stratified_m2.tex`、`fig7_pareto_m2_m1.pdf` |
| `experiments/replay_nr_matrix.py` | `main_seed*_nr.csv`、`table_ii_nr.json` |
| `experiments/reports/build_table_nr_iqa.py` | `latex/sections/table_nr_iqa.tex` |

## τ 消融 Fig.7

```bash
python3 experiments/run_ablation_tau.py
python3 figures/plot_ablation_tau.py
```

## M5 跨集报告

```bash
python3 experiments/cross_dataset_report.py
# -> experiments/results/cross_tcm_fd.json (rho ~ 0.36, n=1144)
```

## 文稿 PDF

```bash
bash ../../scripts/paper1_build_draft.sh
```

## 预期产物

### 标定与主矩阵

- `experiments/results/recommended_tau.json`（τ_B2=0.465，`separation_min_clear_max_blur=-0.541`）
- `experiments/results/recommended_tau_b3.json`（τ_B3=0.5）
- `experiments/results/main_seed{0,1,2}.csv`、`main_seed*_detail.csv`
- `experiments/results/table_ii.json`、`table_ii_bootstrap.json`

### 图表

| 文件 | 论文 Fig. |
|------|-----------|
| `figures/fig_iqa_hist.pdf` | Fig.3（标定重叠直方图） |
| `figures/fig5_rtt_cdf.pdf` | Fig.4（RTT CDF，**simulated latency**） |
| `figures/fig6_valid_rate.pdf` | Fig.5（M2 柱图） |
| `figures/fig7_pareto_m2_m1.pdf` | Fig.6（M2–M1 Pareto） |
| `figures/fig7_ablation_tau.pdf` | Fig.7（τ 消融） |
| `figures/fig_failure_modes_schematic.pdf` | Fig.8（失败模式示意） |
| `figures/fig_s1_franka_rtt.pdf` | Fig.S1（M6 辅轨） |

### LaTeX 表格

- `latex/sections/table_ii.tex`（由 `build_table_ii.py` 生成，**勿手改数字**）
- `latex/sections/table_iii.tex`（B3/B3t/B4）
- `latex/sections/table_stratified_m2.tex`（分层 M2）
- `latex/sections/table_nr_iqa.tex`（BRISQUE/NIQE 附录）
- `latex/main.pdf`、`latex/main-zh.pdf`

## 重要约束

1. **勿将** `franka_m6_rtt.csv` 并入 Table II。
2. 主表 M1 为 **仿真延迟模型**（见 `sim/NETEM.md`），Fig.4/5 图注已标明 simulated latency。
3. `separation_min_clear_max_blur < 0` 表示 clear/blur 分数重叠，**非实现错误**；见 validation 节 Fig.3。

## 无 TCM 全量时的合成路径（legacy）

```bash
python3 scripts/synth_degrade.py
python3 experiments/edge_iqa/calibrate_tau.py
python3 experiments/run_matrix.py --config experiments/configs/main_exp.yaml
```

该路径与 ShezhenV3 主表数字无关，仅用于早期合成验证。
