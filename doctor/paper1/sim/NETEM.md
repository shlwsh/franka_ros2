# 网络延迟模型（离线主实验）

主实验 M1–M3 在 `doctor/paper1` 内通过 **`sim/latency_model.py`** 复现云侧往返延迟，不依赖真实 `netem`。

| 分量 | 模型 | 典型值 (ms) |
|------|------|-------------|
| capture | 常数 | 5 |
| edge_iqa | 高斯 | μ=9, σ=2 |
| route | 常数 | 1.5 |
| resample (edge re-capture) | 对数正态 | p50≈50（主轨 Table II） |
| resample (FR3 motion, 辅轨) | 见 M6 JSONL | 真机闭环，不入 main_exp |
| cloud upload | 均匀 [50, 550] | 0–500ms jitter + 基线 |

WSL 真机复现可选用：

```bash
sudo tc qdisc add dev eth0 root netem delay 100ms 20ms distribution normal
```

论文 **Table II 数字**仅来自 `experiments/run_matrix.py` 输出 CSV，与 franka 辅轨 M6 分离。
