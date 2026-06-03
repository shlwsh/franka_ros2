# 网络延迟模型（离线主实验）

> **更新**：2026-06-04 · 主表 M1 均来自 `sim/latency_model.py`；论文 Fig.4/5 图注标明 **simulated latency model**。

主实验 M1–M3 在 `doctor/paper1` 内通过 **`sim/latency_model.py`** 复现云侧往返延迟，不依赖真实 `netem`。

## 分量模型

| 分量 | 模型 | 典型值 (ms) | 说明 |
|------|------|-------------|------|
| capture | 常数 | 5 | 相机采集 |
| edge_iqa | 高斯 N(μ, σ²) | μ=9, σ=2 | Edge-IQA 打分 |
| route | 常数 | 1.5 | LangGraph 路由决策 |
| resample (edge re-capture) | 对数正态 | p50≈50 | 主轨 Table II 物理重采 |
| resample (FR3 motion, 辅轨) | 见 M6 JSONL | 真机闭环 | **不入** main_exp |
| cloud upload | 均匀 [50, 550] | — | 云 stub 往返 |

完整参数见 `experiments/configs/main_exp.yaml` 与 LaTeX §5.1 setup。

## 与主表的关系

- **Table II 数字**仅来自 `experiments/run_matrix_tcm.py` 输出 CSV。
- **相对排序**（B2 M1 < B0、B2 M2 > B0）在固定模型下成立；**绝对毫秒值**为文档化仿真，非 WAN 实测。
- **M6 Franka 辅轨**使用不同延迟栈（本地 IQA+路由，无云上传仿真），见 `experiments/results/franka_m6_rtt.csv` 与 Fig.S1。

## WSL 真机 netem（可选，非主表数据源）

```bash
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms distribution normal
```

netem 实验用于网络扰动 quick 验证（`scripts/paper1_run_network_quick.sh`），**不写入** Table II。

## 复现检查

```bash
grep -l latency_model experiments/run_matrix_tcm.py
python3 -c "from sim.latency_model import sample_rtt_ms; print('ok')"
```

## 叙述要点（答辩 / Cover Letter）

1. 披露仿真模型，强调 **relative ordering** 而非绝对 WAN RTT。
2. M6 辅轨提供执行栈可行性对冲，**不与主表数值混比**。
3. 物理重采延迟（log-normal p50≈50 ms）与 Skill 变换绑定，非随机 Q uplift。
