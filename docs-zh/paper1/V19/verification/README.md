# 论文 I 阶段验证成果

本目录存放**阶段 1 / 阶段 2** 自动验证报告与原始日志。

| 文档 | 说明 |
|------|------|
| [阶段1-2_验证总览.md](./阶段1-2_验证总览.md) | 两阶段合并结论与复现命令 |
| [阶段1_验证报告.md](./阶段1_验证报告.md) | 系统基座、Skills、Vision 契约、PAPER1_MODE |
| [阶段2_验证报告.md](./阶段2_验证报告.md) | Edge-IQA、τ 标定、延迟、Fig.3 |
| [阶段3_验证报告.md](./阶段3_验证报告.md) | 闭环路由、JSONL、Fig.2 |

**一键复验**：

```bash
cd /root/work/franka_ros2
bash scripts/verify_paper1_phases.sh
```

原始 JSON/日志：`logs/run_*.log`、`logs/*_20260529T084708Z.json`
