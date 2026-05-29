# 论文 I 环境变量（单仓库：franka_ros2）

> 算法与执行均在 **本仓库** 内，无需挂载 `ppt-builder`。

## 路径

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FRANKA_ROS2_ROOT` | `/root/work/franka_ros2` | 本仓库根目录 |
| `PAPER1_ROOT` | `$FRANKA_ROS2_ROOT/doctor/paper1` | 论文 I 算法与实验（`edge_iqa/`、`langgraph_router/` 等） |

```bash
export FRANKA_ROS2_ROOT="/root/work/franka_ros2"
export PAPER1_ROOT="${FRANKA_ROS2_ROOT}/doctor/paper1"
# 可省略：franka_api_server 会自动解析仓库内 doctor/paper1
```

## API

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FRANKA_API_BASE` | `http://127.0.0.1:8000/api/v1` | 边侧 FastAPI |
| `FRANKA_API_KEY` | `franka-api-default-key` | 与 `franka_api_server/config/api_server.yaml` 一致 |

## 论文模式

| 变量 | 说明 |
|------|------|
| `PAPER1_MODE=1` | 禁用 `controller`（刚度/碰撞）路由，仅论文 I 实验 |

## 快速检查

```bash
cd /root/work/franka_ros2
bash scripts/check_paper1_env.sh
```

## 启动顺序（辅轨闭环）

1. `colcon build --symlink-install`（本仓）  
2. `scripts/testall.sh`（MoveIt fake HW + API）  
3. `cd "$PAPER1_ROOT" && python -m langgraph_router.run ...`（阶段 3 起）  
4. 或 `scripts/paper1_closed_loop.sh`（阶段 3 起）
