# 论文 I 双仓环境变量（franka_ros2 ↔ doctor/paper1）

> 配合 [franka_ros2_优化改进计划.md](./franka_ros2_优化改进计划.md) F0-01 使用。

## 路径

| 变量 | WSL 示例 | 说明 |
|------|----------|------|
| `PAPER1_ROOT` | `/mnt/e/work/ppt-builder/doctor/paper1` | 算法仓根目录（须含 `edge_iqa/`、`langgraph_router/`） |
| `FRANKA_ROS2_ROOT` | `/root/work/franka_ros2` | 本仓库根目录 |

Windows 盘挂载：

```bash
# 若 E: 已挂载
export PAPER1_ROOT="/mnt/e/work/ppt-builder/doctor/paper1"
```

## API

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `FRANKA_API_BASE` | `http://127.0.0.1:8000/api/v1` | 边侧 FastAPI |
| `FRANKA_API_KEY` | `franka-api-default-key` | 与 `franka_api_server/config/api_server.yaml` 一致 |

## 论文模式

| 变量 | 说明 |
|------|------|
| `PAPER1_MODE=1` | 计划用于禁用 `controller`（刚度/碰撞）路由，仅论文 I 实验 |

## 快速检查

```bash
cd /root/work/franka_ros2
bash scripts/check_paper1_env.sh   # 待实现；见优化改进计划 F0-03
```

## 启动顺序（辅轨闭环）

1. `colcon build --symlink-install`（本仓）  
2. `scripts/testall.sh`（MoveIt fake HW + API）  
3. `cd "$PAPER1_ROOT" && python -m langgraph_router.run ...`（paper1，待 P3 实现）  
4. 或 `scripts/paper1_closed_loop.sh`（待 F3-01 实现）
