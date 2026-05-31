# Paper II Phase Completion Audit Report

Conservative task-by-task evidence map for the P2-0..P2-6 work plan.

- rows: 35
- phases: 7
- ready: 23
- partial: 11
- blocked: 1
- no submission-required phase task blocked: yes
- reason: no submission-required phase tasks are blocked

| Phase | Ready | Partial | Blocked |
|---|---:|---:|---:|
| P2-0 | 4 | 1 | 0 |
| P2-1 | 4 | 1 | 0 |
| P2-2 | 2 | 3 | 0 |
| P2-3 | 4 | 1 | 0 |
| P2-4 | 5 | 0 | 0 |
| P2-5 | 2 | 3 | 0 |
| P2-6 | 2 | 2 | 1 |

| Phase | Task | Status | Required | Evidence | Reason | Next Action |
|---|---|---|---:|---|---|---|
| P2-0 | P2-0-1 固化本方案与 README | ready | no | docs-zh/paper2/论文II_franka_ros2_科研技术方案与工作计划_20260531.md, docs-zh/paper2/README.md, doctor/paper2/README.md | plan and README files define the Paper II boundary and route | archive evidence |
| P2-0 | P2-0-2 记录 GitNexus 状态 | ready | no | docs-zh/paper2/论文II_franka_ros2_科研技术方案与工作计划_20260531.md | GitNexus index state is recorded in the plan | archive evidence |
| P2-0 | P2-0-3 复核论文 I 当前闭环 | partial | no | scripts/paper1_closed_loop.sh, doctor/paper1/experiments/results/franka_m6_rtt.csv | Paper I loop script and M6 evidence exist, but no fresh Paper II audit reran 10 Paper I trials | rerun or explicitly archive the Paper I loop review for Paper II |
| P2-0 | P2-0-4 确定 doctor/paper2 纳入本仓 | ready | no | doctor/paper2 | doctor/paper2 is present and separated from ROS packages | archive evidence |
| P2-0 | P2-0-5 建立 secrets 规则 | ready | yes | plan/README | secrets and clinical-data exclusion rules are documented | archive evidence |
| P2-1 | P2-1-1 新建 doctor/paper2 骨架 | ready | no | 26 test file(s) | Paper II package skeleton and tests exist | archive evidence |
| P2-1 | P2-1-2 定义 Paper2State | ready | no | doctor/paper2/langgraph_router/state.py | Paper2State covers identity, KG, FHIR, and latency fields | archive evidence |
| P2-1 | P2-1-3 实现规则路由 | partial | no | doctor/paper2/langgraph_router/routing.py | routing covers 6/7 planned route decisions | add missing route decisions and tests |
| P2-1 | P2-1-4 实现单 trial runner | ready | no | doctor/paper2/langgraph_router/run.py; rows=120 | single-trial runner generated JSONL evidence | archive evidence |
| P2-1 | P2-1-5 复用 franka client | ready | no | doctor/paper2/tools/franka_client.py | Franka API client exposes vision and skill calls | archive evidence |
| P2-2 | P2-2-1 小型 KG schema | partial | yes | doctor/paper2/kg/kg_stub.json; entities=10; edges=0 | KG stub exists but is below the 30-entity plan target | extend KG entity coverage |
| P2-2 | P2-2-2 实体归一化 | ready | yes | doctor/paper2/tools/entity_normalizer.py | standalone entity normalizer exists | archive evidence |
| P2-2 | P2-2-3 gamma_conflict 计算 | ready | no | doctor/paper2/agents/kg_conflict_agent.py, doctor/paper2/tests/test_kg_conflict.py | gamma_conflict computation and tests exist | archive evidence |
| P2-2 | P2-2-4 冲突注入脚本 | partial | no | doctor/paper2/experiments/results/conflict_detection.csv | conflict outcomes exist, but there is no standalone inject_conflicts.py script | factor synthetic conflict construction into inject_conflicts.py |
| P2-2 | P2-2-5 B0/B1/B2 对比 | partial | no | conflict_detection.csv; B0_F1=0.7500; B2_F1=1.0000 | B2 improves F1 over B0, but no KG gate AUC table is present | add kg_gate_auc.csv or report why AUC is out of scope |
| P2-3 | P2-3-1 扩展 Skills 清单 | partial | yes | poses.yaml | existing tongue/face skills are present, but planned resample skills are not configured | add and validate fake-hardware resample skills |
| P2-3 | P2-3-2 Action Agent 工具选择 | ready | no | doctor/paper2/agents/action_agent.py, doctor/paper2/tests/test_pipeline.py | Action Agent selects tool calls in low-quality cases | archive evidence |
| P2-3 | P2-3-3 closed-loop 脚本 | ready | no | scripts/paper2_closed_loop.sh; jsonl_rows=120 | Paper II closed-loop script generates JSONL evidence | archive evidence |
| P2-3 | P2-3-4 M6 风格 RTT 汇总 | ready | no | doctor/paper2/experiments/summarize_closed_loop.py, doctor/paper2/experiments/results/closed_loop_summary.csv; rows=120; summary_rows=6 | M6-style latency summarizer reports p50/p95 and route distribution | archive evidence |
| P2-3 | P2-3-5 安全退出 | ready | yes | routing.py | retry-based human_review/fail_safe routing is implemented | archive evidence |
| P2-4 | P2-4-1 EMR draft schema | ready | no | doctor/paper2/schemas/emr_draft.schema.json | EMR draft JSON schema exists | archive evidence |
| P2-4 | P2-4-2 FHIR mapping MVP | ready | no | doctor/paper2/agents/emr_fhir_agent.py | EMR/FHIR agent builds minimal document Bundle resources | archive evidence |
| P2-4 | P2-4-3 FHIR validator wrapper | ready | yes | doctor/paper2/tools/fhir_validator.py, doctor/paper2/tests/test_fhir_validator.py | FHIR validator wrapper and tests exist | archive evidence |
| P2-4 | P2-4-4 repair loop | ready | no | doctor/paper2/agents/emr_fhir_agent.py; B2=0.2500; B4=0.6250 | repair loop improves FHIR validity | archive evidence |
| P2-4 | P2-4-5 输出脱敏样例 | ready | yes | doctor/paper2/experiments/samples/paper2_run_001.sample.jsonl, doctor/paper2/datasets/samples/paper2_cases.sample.csv | tracked samples are synthetic/no-PHI artifacts | archive evidence |
| P2-5 | P2-5-1 B0-B4 全量实验 | partial | no | paper2_summary.csv; baselines=5 | B0-B4 results exist for one deterministic synthetic run, but not 3 seeds | add multi-seed experiment matrix |
| P2-5 | P2-5-2 工具调用有效性统计 | ready | no | doctor/paper2/experiments/results/tool_ablation.csv | tool-call effectiveness table exists | archive evidence |
| P2-5 | P2-5-3 幻觉率评估 | partial | no | doctor/paper2/experiments/results/paper2_summary.csv | hallucination rates are in summary CSV, but standalone hallucination_eval.csv is missing | export hallucination_eval.csv with fixed annotation rules |
| P2-5 | P2-5-4 图表脚本 | ready | no | doctor/paper2/figures/plot_results.py, doctor/paper2/figures/paper2_summary_metrics.svg | figure script and rendered figures exist | archive evidence |
| P2-5 | P2-5-5 初稿结果段 | partial | no | doctor/paper2/latex/main.tex | results are present in monolithic LaTeX, but latex/sections/results.tex is missing | split manuscript into section files before submission |
| P2-6 | P2-6-1 方法章节初稿 | partial | no | doctor/paper2/latex/main.tex | method content exists in monolithic LaTeX | split method.tex |
| P2-6 | P2-6-2 系统章节 | ready | no | doctor/paper2/latex/sections/system.tex | standalone system section exists | archive evidence |
| P2-6 | P2-6-3 专利交底 | blocked | no | doctor/paper2/patent/paper2_disclosure.md | Paper II patent disclosure is missing | draft conflict-gating/self-healing disclosure |
| P2-6 | P2-6-4 复现实验说明 | ready | no | doctor/paper2/REPRODUCE.md | third-party synthetic MVP reproduction instructions exist | archive evidence |
| P2-6 | P2-6-5 投稿路线复核 | partial | yes | REPRODUCE.md, bilingual drafts | submission blockers are documented, but no target journal/ethics checklist is finalized | add target journal and ethics/data-license checklist |
