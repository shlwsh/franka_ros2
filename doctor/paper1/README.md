# Paper I — Edge-IQA + LangGraph

论文 I 算法与实验代码，与 `franka_ros2` **同仓库**管理。

## 路径

| 变量 | 默认值 |
|------|--------|
| `PAPER1_ROOT` | `<franka_ros2>/doctor/paper1` |
| `FRANKA_ROS2_ROOT` | 本仓库根目录 |

无需挂载 `ppt-builder`；克隆本仓库即可。

```bash
export PAPER1_ROOT="/root/work/franka_ros2/doctor/paper1"
# 或省略（franka_api_server 自动解析仓库内路径）
```

## 目录

| 路径 | 说明 |
|------|------|
| `edge_iqa/` | 边侧 IQA（阶段 2） |
| `langgraph_router/` | 置信度路由（阶段 3） |
| `sim/franka_bridge/` | HTTP 客户端 |
| `experiments/` | 日志、CSV、debug 图像 |
| `figures/` | 论文图 |
| `latex/sections/` | LaTeX 节草稿 |

## 与 franka_api_server 的关系

- **算法不进 ROS**：`edge_iqa`、`langgraph_router` 仅在本目录。
- **执行在** `franka_api_server`：vision / skills / motion HTTP。
- 设置 `PAPER1_MODE=1` 禁用阻抗类 API。

## Edge-IQA（阶段 2）

```bash
cd /root/work/franka_ros2/doctor/paper1
pip install -r requirements-paper1.txt   # numpy, Pillow, matplotlib
python3 scripts/synth_degrade.py         # 合成 val 集（无 TCM 时）
python3 -m pytest edge_iqa/tests -q
python3 experiments/edge_iqa/calibrate_tau.py
python3 experiments/edge_iqa/latency_benchmark.py
python3 figures/plot_iqa_hist.py
```

推荐阈值：**τ ≈ 0.505**（见 `experiments/results/recommended_tau.json`）。  
离线 scorer **p95 ≈ 8.7 ms** @512px（`experiments/edge_iqa/latency_benchmark.json`）。

## 闭环路由（阶段 3）

```bash
cd /root/work/franka_ros2
bash scripts/paper1_closed_loop.sh
python3 scripts/validate_jsonl.py doctor/paper1/experiments/logs/run_001.jsonl
```

## 主实验与文稿（阶段 4–5）

```bash
bash scripts/paper1_run_main.sh      # Table II / Fig.5–6
bash scripts/paper1_run_m6.sh        # 辅轨 Fig.S1
bash scripts/paper1_build_draft.sh   # Fig.7 + main.pdf
```

复现说明：`REPRODUCE.md`；Franka 栈见 `docs-zh/paper1/V19/REPRODUCE_franka.md`。

## 快速检查

```bash
cd /root/work/franka_ros2
bash scripts/check_paper1_env.sh
```
