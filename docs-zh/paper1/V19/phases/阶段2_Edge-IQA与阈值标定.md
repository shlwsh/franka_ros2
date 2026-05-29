# 阶段 2：Edge-IQA 与阈值标定

> **周期**：W2–W3（约 8–10 个 AI 工作日）  
> **前置**：[阶段1](./阶段1_系统基座与架构证据.md) 验收通过  
> **科研问题**：边侧图像质量评分是否 **有判别力、可标定 τ、满足实时性（p95&lt;30ms）**？

---

## 1. 科研成果对齐

| 论文要素 | 本阶段产出 | 验收标准 |
|----------|------------|----------|
| **§4.1 Edge-IQA** | `latex/sections/04_1_edge_iqa.tex` | 含 Q 公式、算法伪代码、复杂度一句 |
| **Fig.3** IQA 分布 | `figures/fig_iqa_hist.pdf` | val 集清晰/模糊分布可区分 |
| **阈值 τ** | `experiments/results/calibration_val.csv` + 文档推荐 τ | 与路由节点默认一致（如 0.55） |
| **指标** | P2-T03：`latency_benchmark.json` | CPU p95 &lt;30ms @512×512 |
| **边侧挂载** | `POST /vision/evaluate` 实装 | 与离线 scorer 同分布（抽样 20 张） |
| **M5 初稿**（可选） | `reports/cross_dataset.md` | Spearman 或定性一段，可阶段 5 补强 |

---

## 2. AI 任务分解

### 2.1 paper1 算法（主）

| 序 | 任务 | 说明 |
|----|------|------|
| 1 | `edge_iqa/scorer.py` | Laplacian + 曝光融合（或 V19 既定公式） |
| 2 | `edge_iqa/tests/test_scorer.py` | 清晰 vs 模糊均值差 &gt;0.2 |
| 3 | `edge_iqa/cli.py` | `--image PATH --json` 供子进程 |
| 4 | `experiments/edge_iqa/calibrate_tau.py` | 扫 val → 推荐 τ |
| 5 | `experiments/edge_iqa/latency_benchmark.py` | 100 张 → JSON |
| 6 | Fig.3 绘图脚本 | `figures/plot_iqa_hist.py` |

**数据策略（压缩）**：

- 若 TCM 全量未就绪：使用 `splits/val.json` **≥200 张** 种子 + `scripts/synth_degrade.py` 生成 blur/exposure 对照。  
- 全量下载与学生并行，**不阻塞** 本阶段闸门。

### 2.2 franka_ros2 边侧

| 序 | 任务 | 文件 |
|----|------|------|
| 1 | `services/paper1_iqa.py` 子进程 | 调用 `python -m edge_iqa.cli` |
| 2 | vision 路由实装 | `routers/vision.py` |
| 3 | `test_vision.py` mock + 降级 | CI 无 PAPER1_ROOT |
| 4 | `scripts/paper1_iqa_bench.sh` | API 路径 p95 报告 |
| 5 | `debug=true` 缓存目录 | `logs/paper1_iqa/` |

---

## 3. 交付工件

```
paper1/
  edge_iqa/scorer.py, cli.py, tests/
  experiments/results/calibration_val.csv
  experiments/edge_iqa/latency_benchmark.json
  figures/fig_iqa_hist.pdf
  latex/sections/04_1_edge_iqa.tex

franka_ros2/
  services/paper1_iqa.py
  test/test_vision.py
  scripts/paper1_iqa_bench.sh
```

---

## 4. 验收命令

```bash
# 离线 scorer
cd "$PAPER1_ROOT" && python -m pytest edge_iqa/tests -q
python -m edge_iqa.cli --image experiments/debug/sample_clear.png --json
python experiments/edge_iqa/latency_benchmark.py

# API
export PAPER1_MODE=1
bash /root/work/franka_ros2/scripts/paper1_iqa_bench.sh
# 期望：api_p95_ms < 35（含 HTTP 开销可略放宽，scorer 本体 <30）
```

---

## 5. 学生检查点

- [x] 合成 val：`experiments/splits/val.json`（240 条）  
- [x] 抽检 5 张：clear 0.80–0.84，blur 0.18–0.20（见 [../verification/阶段2_验证报告.md](../verification/阶段2_验证报告.md)）  

---

## 6. 阶段完成 checklist

- [x] P2-T01～P2-T04、F2-01～F2-04  
- [x] Fig.3 + §4.1 tex  
- [x] 总纲 §8 阶段 2 闸门  

**下一阶段**：[阶段3_闭环路由与可复现日志.md](./阶段3_闭环路由与可复现日志.md)
