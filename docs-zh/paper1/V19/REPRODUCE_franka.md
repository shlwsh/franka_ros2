# Paper I — Franka 栈第三方复现（≥10 trial）

> 算法在 `doctor/paper1`；执行在 `franka_ros2` + `franka_api_server`。  
> 主表数字来自离线 `run_matrix`，本指南仅复现 **闭环执行栈**。

## 1. 前置

```bash
git clone <franka_ros2_url> && cd franka_ros2
vcs import src < src/dependency.repos --recursive --skip-existing
rosdep install --from-paths src --ignore-src --rosdistro humble -y
colcon build --symlink-install --packages-select franka_api_server
source install/setup.bash
```

```bash
export PAPER1_ROOT="$PWD/doctor/paper1"
python3 -m pip install -r doctor/paper1/requirements-paper1.txt
bash scripts/check_paper1_env.sh
```

## 2. 模式

```bash
export PAPER1_MODE=1
export FRANKA_API_KEY=franka-api-default-key
```

`PAPER1_MODE=1` 禁用阻抗类 controller API（论文边界）。

## 3. 闭环 10 trial（最小验收）

```bash
export TRIALS=10
bash scripts/paper1_closed_loop.sh
python3 scripts/validate_jsonl.py "$PAPER1_ROOT/experiments/logs/run_001.jsonl"
```

预期：`run_001.jsonl` ≥10 行；`route_decision` 含 `upload_cloud` 与 `resample_edge`。

## 4. 辅轨 M6（可选 50 trial）

```bash
bash scripts/paper1_run_m6.sh
```

产出：`experiments/results/franka_m6_rtt.csv`（**不入主表**）。

## 5. API 烟测（无 MoveIt 时）

```bash
ros2 launch franka_fr3_moveit_config moveit.launch.py use_fake_hardware:=true robot_ip:=dont-care &
export FRANKA_API_PORT=8000
ros2 launch franka_api_server api_server.launch.py
curl -s "http://127.0.0.1:8000/api/v1/motion/skills?api_key=$FRANKA_API_KEY"
curl -s -X POST "http://127.0.0.1:8000/api/v1/vision/evaluate?api_key=$FRANKA_API_KEY" \
  -F "file=@$PAPER1_ROOT/experiments/synthetic/clear/clear_0000.png"
```

## 6. 故障排查

| 现象 | 处理 |
|------|------|
| skill motion `failed` | 需 MoveIt / fake HW 运行 |
| vision 超时 | 检查 `PAPER1_ROOT` 与 `edge_iqa` 依赖 |
| controller 404 | `PAPER1_MODE=1` 下为预期 |

## 7. 与离线主实验关系

主表 M1–M3：`bash scripts/paper1_run_main.sh`（见 `doctor/paper1/REPRODUCE.md`）。
