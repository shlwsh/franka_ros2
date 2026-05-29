# franka_ros2 论文 I 辅轨 — 研发任务清单

> **版本**：V19-tasks-1 | 2026-05-29  
> **⚠️ 执行以 AI 压缩计划为准**：[AI科研执行总纲_V19.md](./AI科研执行总纲_V19.md) + [phases/](./phases/) 五阶段科研安排  
> **技术方案**：[franka_ros2_技术实现方案.md](./franka_ros2_技术实现方案.md)  
> **总任务 DAG**：[论文1_V19_tasks.json](./论文1_V19_tasks.json)  
> **投稿截止**：2026-09-30

下文 Sprint 0–4 保留作 **文件级对照**；阶段划分、科研成果对齐见 `phases/阶段*.md`。

**图例**：`[ ]` 待办 · `[~]` 进行中 · `[x]` 完成 · **P0** 阻塞后续 · 工时为人日（1人日≈6h 专注开发）

---

## 0. 里程碑对照

| 里程碑 | 日期 | franka_ros2 必达 |
|--------|------|------------------|
| M0 | 2026-06-30 | F0 完成 + testall 稳定 |
| M-alpha | 2026-07-31 | F1 + F2（IQA API p95&lt;30ms） |
| M-beta | 2026-08-15 | F3（10 trial JSONL + 50 trial M6） |
| M-gamma | 2026-08-31 | F4 复现文档 + 样例 JSONL |
| M-sigma | 2026-09-30 | 验收总表全绿 |

---

## Sprint 0（W1，~06.01–06.07）— 环境与论文模式

| ID | 任务 | 优先级 | 工时 | 依赖 | 负责人 | 状态 |
|----|------|--------|------|------|--------|------|
| S0-1 | 确认 `PAPER1_ROOT` 挂载，更新 [ENV.md](./ENV.md) 实机路径 | P0 | 0.5 | — | 学生 | [ ] |
| S0-2 | `colcon build --symlink-install` 通过并记录命令 | P0 | 0.5 | S0-1 | 学生 | [ ] |
| S0-3 | `scripts/testall.sh` 通过，`curl` API 200 | P0 | 0.5 | S0-2 | 学生 | [ ] |
| S0-4 | `config.py` 增加 `paper1_mode`, `paper1_root` | P0 | 0.5 | — | AI | [ ] |
| S0-5 | `app.py`：`PAPER1_MODE=1` 时不注册 controller | P0 | 0.5 | S0-4 | AI | [ ] |
| S0-6 | `check_paper1_env.sh`：vision/skills 检查改为硬失败（实现后） | P1 | 0.25 | S0-4 | AI | [ ] |
| S0-7 | 运行 `check_paper1_env.sh` 并截图存档（M0 证据） | P1 | 0.25 | S0-3 | 学生 | [ ] |

**Sprint 0 验收**：F0-01～F0-03 对应 [优化改进计划](./franka_ros2_优化改进计划.md) §4 Phase F0。

---

## Sprint 1（W2–W3，~06.08–06.21）— F1 Skills + Vision 占位

| ID | 任务 | 优先级 | 工时 | 依赖 | 负责人 | 状态 |
|----|------|--------|------|------|--------|------|
| S1-1 | 新建 `skills/poses.yaml`（tongue_pose, face_pose） | P0 | 1 | S0-3 | AI | [ ] |
| S1-2 | RViz 标定关节角并回写 yaml | P0 | 1 | S1-1 | 学生 | [ ] |
| S1-3 | 实现 `services/skills_loader.py` | P0 | 0.5 | S1-1 | AI | [ ] |
| S1-4 | `POST /motion/skills/{skill_name}` | P0 | 0.5 | S1-3 | AI | [ ] |
| S1-5 | `test_api.py` 增加 skills 用例 | P1 | 0.5 | S1-4 | AI | [ ] |
| S1-6 | 新建 `models/vision.py` + `routers/vision.py` 占位 | P0 | 1 | S0-5 | AI | [ ] |
| S1-7 | `app.py` 注册 vision 路由 | P0 | 0.25 | S1-6 | AI | [ ] |
| S1-8 | 更新 `docs-api/api_specification.md` | P1 | 0.5 | S1-6 | AI | [ ] |
| S1-9 | `scripts/paper1_gazebo_capture.sh` + 相机 topic 文档化 | P1 | 1.5 | S0-3 | 学生 | [ ] |
| S1-10 | 首张 `capture_001.png` 落到 `$PAPER1_ROOT/experiments/debug/` | P1 | 0.5 | S1-9 | 学生 | [ ] |
| S1-11 | `testall.sh --paper1` 快速检查（可选） | P2 | 0.5 | S1-4,S1-6 | AI | [ ] |

**Sprint 1 验收**：F1-01～F1-05；对应 tasks.json `F1-01`, `P1-T02`（占位）, `P1-T03`。

---

## Sprint 2（W4–W6，~06.22–07.12）— F2 Edge-IQA 挂载

| ID | 任务 | 优先级 | 工时 | 依赖 | 负责人 | 状态 |
|----|------|--------|------|------|--------|------|
| S2-0 | **paper1** P2-T01 scorer 可 import（阻塞） | P0 | — | P0 数据 | 学生 | [ ] |
| S2-1 | `services/paper1_iqa.py` 子进程调用 | P0 | 1.5 | S2-0, S1-6 | AI | [ ] |
| S2-2 | vision 路由接入实装 scorer | P0 | 0.5 | S2-1 | AI | [ ] |
| S2-3 | 响应字段对齐 LangGraph TypedDict | P0 | 0.5 | S2-2 | AI | [ ] |
| S2-4 | `debug=true` → `logs/paper1_iqa/` | P2 | 0.5 | S2-2 | AI | [ ] |
| S2-5 | `test/test_vision.py`（mock + 无 PAPER1_ROOT 降级） | P0 | 1 | S2-2 | AI | [ ] |
| S2-6 | `scripts/paper1_iqa_bench.sh` + p95 报告 | P0 | 0.5 | S2-2 | 学生 | [ ] |
| S2-7 | 与 P2-T03 对比：API 路径 p95&lt;30ms | P0 | 0.5 | S2-6 | 学生 | [ ] |

**Sprint 2 验收**：F2-01～F2-04；tasks.json `F2-01`。

---

## Sprint 3（W7–W9，~07.13–08.02）— F3 闭环与 M6

| ID | 任务 | 优先级 | 工时 | 依赖 | 负责人 | 状态 |
|----|------|--------|------|------|--------|------|
| S3-0 | **paper1** P3-T01/T02 LangGraph 图 | P0 | — | P2 | 学生 | [ ] |
| S3-1 | **paper1** `sim/franka_bridge/client.py` | P0 | 1.5 | S1-6,S1-4 | 学生 | [ ] |
| S3-2 | **paper1** `langgraph_router.run` + JSONL 写入 | P0 | 2 | S3-0,S3-1 | 学生 | [ ] |
| S3-3 | `scripts/paper1_closed_loop.sh` | P0 | 0.5 | S3-2, S0-3 | AI | [ ] |
| S3-4 | 10 trial → `run_001.jsonl` | P0 | 0.5 | S3-3 | 学生 | [ ] |
| S3-5 | 校验 JSONL 字段完整性脚本 | P1 | 0.5 | S3-4 | AI | [ ] |
| S3-6 | `scripts/paper1_run_m6.sh`（50 trial） | P0 | 0.5 | S3-4 | AI | [ ] |
| S3-7 | 生成 `franka_m6_rtt.csv` + p50/p95 | P0 | 0.5 | S3-6 | 学生 | [ ] |
| S3-8 | Fig.S1 草图（由 CSV 绘制，paper1 figures） | P2 | 1 | S3-7 | 学生 | [ ] |

**Sprint 3 验收**：F3-01～F3-04；tasks.json `F3-01`, `P3-T03`。

---

## Sprint 4（W10–W12，~08.03–08.25）— F4 交付与硬化

| ID | 任务 | 优先级 | 工时 | 依赖 | 负责人 | 状态 |
|----|------|--------|------|------|--------|------|
| S4-1 | 编写 `REPRODUCE_franka.md` | P0 | 1 | S3-4 | AI | [ ] |
| S4-2 | `requirements-paper1.txt` pin 依赖 | P1 | 0.25 | — | AI | [ ] |
| S4-3 | 脱敏 `run_001.sample.jsonl` 入 `samples/` | P1 | 0.5 | S3-4 | 学生 | [ ] |
| S4-4 | 第三方按文档复现 10 trial（他人机器试跑） | P0 | 1 | S4-1 | 学生 | [ ] |
| S4-5 | 确认论文实验未调用 stiffness API（审计 grep） | P0 | 0.25 | S0-5 | AI | [ ] |
| S4-6 | 分支 `paper1/*` 合并策略与 CHANGELOG 条目 | P2 | 0.5 | S4-4 | 学生 | [ ] |

**Sprint 4 验收**：F4-01～F4-04；[优化改进计划](./franka_ros2_优化改进计划.md) §11 验收总表。

---

## 1. 文件级 Checklist（研发勾选）

### franka_api_server

- [ ] `config.py` — PAPER1_* 配置项
- [ ] `app.py` — 条件 controller、注册 vision
- [ ] `skills/poses.yaml`
- [ ] `services/skills_loader.py`
- [ ] `services/paper1_iqa.py`
- [ ] `routers/motion.py` — skills 端点
- [ ] `routers/vision.py`
- [ ] `models/vision.py`
- [ ] `models/motion.py` — 可选时间戳字段
- [ ] `test/test_vision.py`
- [ ] `test/test_api.py` — skills 用例
- [ ] `docs-api/api_specification.md`

### scripts

- [ ] `check_paper1_env.sh` — 随阶段更新
- [ ] `paper1_gazebo_capture.sh`
- [ ] `paper1_iqa_bench.sh`
- [ ] `paper1_closed_loop.sh`
- [ ] `paper1_run_m6.sh`

### docs-zh/paper1/V19

- [x] `ENV.md`
- [ ] `REPRODUCE_franka.md`
- [x] `franka_ros2_技术实现方案.md`
- [x] `franka_ros2_研发任务清单.md`
- [ ] `samples/run_001.sample.jsonl`

---

## 2. 与 paper1 协作任务（非本仓编码，但阻塞 franka）

| paper1 任务 | 阻塞的 franka 任务 | 最晚对齐日 |
|-------------|-------------------|------------|
| P2-T01 scorer | S2-1～S2-7 | 07-05 |
| P2-T03 latency bench | S2-7 | 07-12 |
| P3-T01/T02 LangGraph | S3-2 | 07-20 |
| P3-T03 franka_bridge | S3-1, S3-3 | 07-28 |
| P1-T03 PNG | S1-10 | 06-21 |

**周会检查**：paper1 与 franka 各报 `PAPER1_ROOT` / API 端口 / 最近一次 JSONL 行数。

---

## 3. Git 分支建议

| 分支 | 内容 |
|------|------|
| `paper1/f0-env` | S0-4～S0-6 |
| `paper1/f1-skills-vision` | S1-* |
| `paper1/f2-iqa` | S2-* |
| `paper1/f3-closed-loop` | S3-3, S3-6 |
| `paper1/f4-reproduce` | S4-* |

提交前缀：`feat(paper1):`、`test(paper1):`、`docs(paper1):`。

---

## 4. 验收总表（投稿前复制到 PR / 课题周报）

- [ ] F0：`PAPER1_ROOT` 可读，`testall.sh` 稳定
- [ ] F1：`go_to_tongue_pose` / `go_to_face_pose` API 可达
- [ ] F1：`POST /vision/evaluate` 契约稳定（占位→实装）
- [ ] F2：边侧 IQA p95 &lt;30ms（与 P2-T03 一致）
- [ ] F3：`paper1_closed_loop.sh` ≥10 行 JSONL
- [ ] F3：M6 共 50 trial，`franka_m6_rtt.csv` 可绘图
- [ ] 论文 I 未调用 stiffness/collision API
- [ ] `REPRODUCE_franka.md` 第三方可复现

---

## 5. 近期 5 个工作日（可直接开工）

| 日 | 任务 ID | 动作 |
|----|---------|------|
| D1 | S0-1～S0-3 | 挂载、构建、testall |
| D2 | S0-4～S0-6 | 论文模式 + env 检查 |
| D3 | S1-1～S1-4 | poses + skills API |
| D4 | S1-6～S1-8 | vision 占位 + 文档 |
| D5 | S1-2,S1-9 | RViz 标定 + Gazebo 首张 PNG |

---

## 6. 状态同步

- 完成项请更新本文件 `[ ]` → `[x]`，并同步 [论文1_V19_tasks.json](./论文1_V19_tasks.json) 中 `F0-*` / `F1-*` / `F2-*` / `F3-*` 的 `status` 字段。
- 重大契约变更须同时改：技术实现方案 §5、优化改进计划 §5、`api_specification.md`。

---

*准备进入研发：从 **Sprint 0 / S0-1** 开始；AI 可并行 **S0-4、S0-5** 与 **S1-3、S1-4** 的骨架代码（vision 占位可在 poses 标定前合并）。*
