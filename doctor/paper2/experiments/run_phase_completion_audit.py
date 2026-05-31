"""Audit Paper II phase-task completion against the 2026-05-31 work plan.

The audit maps each P2-0..P2-6 task to concrete repository evidence. It is not
a submission-readiness claim; blocked rows are expected for tasks that require
controlled data, licensed ontology assets, online robot evidence, or real
expert participation.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_OUT = ROOT / "experiments" / "results" / "phase_completion_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "phase_completion_audit_report.md"
PLAN_PATH = REPO_ROOT / "docs-zh" / "paper2" / "论文II_franka_ros2_科研技术方案与工作计划_20260531.md"

STATUS_READY = "ready"
STATUS_PARTIAL = "partial"
STATUS_BLOCKED = "blocked"
VALID_STATUSES = {STATUS_READY, STATUS_PARTIAL, STATUS_BLOCKED}

FIELDNAMES = [
    "phase",
    "task_id",
    "task",
    "status",
    "required_for_submission",
    "evidence",
    "reason",
    "next_action",
]


@dataclass(frozen=True)
class PhaseTask:
    phase: str
    task_id: str
    task: str
    required_for_submission: bool
    evaluator: Callable[[], tuple[str, str, str, str]]


@dataclass(frozen=True)
class PhaseAuditValidation:
    ready: bool
    rows: int
    ready_rows: int
    partial_rows: int
    blocked_rows: int
    phases: int
    reason: str


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _exists(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8") if path.is_file() else ""


def _csv_rows(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def _json_obj(path: Path) -> Any:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _jsonl_count(path: Path) -> int:
    if not path.is_file():
        return 0
    with path.open(encoding="utf-8") as f:
        return sum(1 for line in f if line.strip())


def _row_status_from_csv(path: Path, *, min_rows: int = 1) -> bool:
    return len(_csv_rows(path)) >= min_rows


def _ready(evidence: str, reason: str, next_action: str = "archive evidence") -> tuple[str, str, str, str]:
    return STATUS_READY, evidence, reason, next_action


def _partial(evidence: str, reason: str, next_action: str) -> tuple[str, str, str, str]:
    return STATUS_PARTIAL, evidence, reason, next_action


def _blocked(evidence: str, reason: str, next_action: str) -> tuple[str, str, str, str]:
    return STATUS_BLOCKED, evidence, reason, next_action


def _plan_and_docs() -> tuple[str, str, str, str]:
    docs = [
        PLAN_PATH,
        REPO_ROOT / "docs-zh" / "paper2" / "README.md",
        ROOT / "README.md",
    ]
    if all(_exists(path) for path in docs):
        return _ready(
            ", ".join(_display_path(path) for path in docs),
            "plan and README files define the Paper II boundary and route",
        )
    missing = [path for path in docs if not _exists(path)]
    return _blocked(
        ", ".join(_display_path(path) for path in missing),
        "required plan/index files are missing",
        "restore plan and README files",
    )


def _gitnexus_status_recorded() -> tuple[str, str, str, str]:
    text = _read_text(PLAN_PATH)
    markers = ("6214 symbols", "156 execution flows", "up-to-date")
    if all(marker in text for marker in markers):
        return _ready(_display_path(PLAN_PATH), "GitNexus index state is recorded in the plan")
    return _partial(
        _display_path(PLAN_PATH),
        "plan exists but GitNexus status markers are incomplete or stale",
        "refresh GitNexus status and update the plan or weekly report",
    )


def _paper1_loop_reviewed() -> tuple[str, str, str, str]:
    script = REPO_ROOT / "scripts" / "paper1_closed_loop.sh"
    m6 = REPO_ROOT / "doctor" / "paper1" / "experiments" / "results" / "franka_m6_rtt.csv"
    if _exists(script) and _exists(m6):
        return _partial(
            f"{_display_path(script)}, {_display_path(m6)}",
            "Paper I loop script and M6 evidence exist, but no fresh Paper II audit reran 10 Paper I trials",
            "rerun or explicitly archive the Paper I loop review for Paper II",
        )
    return _blocked(
        _display_path(script),
        "Paper I closed-loop review evidence is missing",
        "run paper1_closed_loop.sh or record a blocking note",
    )


def _paper2_directory_strategy() -> tuple[str, str, str, str]:
    if (ROOT / "langgraph_router").is_dir() and (ROOT / "README.md").is_file():
        return _ready(_display_path(ROOT), "doctor/paper2 is present and separated from ROS packages")
    return _blocked(_display_path(ROOT), "doctor/paper2 research layer is missing", "restore research layer")


def _secrets_rule() -> tuple[str, str, str, str]:
    joined = "\n".join(_read_text(path) for path in [PLAN_PATH, ROOT / "README.md"])
    if re.search(r"passwords?, API keys?|密码|API Key", joined, flags=re.I):
        return _ready("plan/README", "secrets and clinical-data exclusion rules are documented")
    return _blocked("plan/README", "secrets rule is not documented", "document secret-handling rules")


def _skeleton_tests() -> tuple[str, str, str, str]:
    tests = sorted((ROOT / "tests").glob("test_*.py"))
    if tests and (ROOT / "__init__.py").is_file():
        return _ready(f"{len(tests)} test file(s)", "Paper II package skeleton and tests exist")
    return _blocked(_display_path(ROOT / "tests"), "test skeleton is missing", "add package skeleton and tests")


def _state_object() -> tuple[str, str, str, str]:
    path = ROOT / "langgraph_router" / "state.py"
    text = _read_text(path)
    required = ["Paper2State", "trial_id", "case_id", "gamma_conflict", "fhir_bundle", "latency_ms"]
    if all(item in text for item in required):
        return _ready(_display_path(path), "Paper2State covers identity, KG, FHIR, and latency fields")
    return _blocked(_display_path(path), "Paper2State does not cover the planned minimum fields", "complete state fields")


def _routing_rules() -> tuple[str, str, str, str]:
    path = ROOT / "langgraph_router" / "routing.py"
    text = _read_text(path)
    routes = ["generate_emr", "resample_vision", "ask_followup", "query_kg", "repair_fhir", "human_review", "fail_safe"]
    present = [route for route in routes if route in text]
    if len(present) == len(routes):
        return _ready(_display_path(path), "routing enumerates all planned route decisions")
    if present:
        return _partial(
            _display_path(path),
            f"routing covers {len(present)}/{len(routes)} planned route decisions",
            "add missing route decisions and tests",
        )
    return _blocked(_display_path(path), "routing rules are missing", "implement rule routing")


def _runner_jsonl() -> tuple[str, str, str, str]:
    run_path = ROOT / "langgraph_router" / "run.py"
    log_path = ROOT / "experiments" / "logs" / "paper2_run_001.jsonl"
    rows = _jsonl_count(log_path)
    if _exists(run_path) and rows >= 10:
        return _ready(f"{_display_path(run_path)}; rows={rows}", "single-trial runner generated JSONL evidence")
    return _blocked(
        f"{_display_path(run_path)}; rows={rows}",
        "runner or JSONL evidence is missing",
        "run python3 -m doctor.paper2.langgraph_router.run --trials 10",
    )


def _franka_client() -> tuple[str, str, str, str]:
    path = ROOT / "tools" / "franka_client.py"
    text = _read_text(path)
    has_vision = "evaluate_image" in text or "evaluate_image_path" in text
    has_skill = "execute_skill" in text or "go_to_skill" in text
    if has_vision and has_skill:
        return _ready(_display_path(path), "Franka API client exposes vision and skill calls")
    return _blocked(_display_path(path), "Franka client lacks required tool calls", "add evaluate_image and execute_skill")


def _kg_schema() -> tuple[str, str, str, str]:
    path = ROOT / "kg" / "kg_stub.json"
    obj = _json_obj(path) or {}
    entities = obj.get("entities") if isinstance(obj, dict) else []
    edges = obj.get("edges") if isinstance(obj, dict) else []
    count = len(entities or [])
    edge_count = len(edges or [])
    evidence = f"{_display_path(path)}; entities={count}; edges={edge_count}"
    if count >= 30:
        return _ready(evidence, "small KG schema meets the 30-entity target")
    if count > 0:
        return _partial(evidence, "KG stub exists but is below the 30-entity plan target", "extend KG entity coverage")
    return _blocked(evidence, "KG schema is missing or empty", "create KG stub")


def _entity_normalizer() -> tuple[str, str, str, str]:
    path = ROOT / "tools" / "entity_normalizer.py"
    if path.is_file():
        return _ready(_display_path(path), "standalone entity normalizer exists")
    symptom_agent = ROOT / "agents" / "symptom_agent.py"
    if "normalize" in _read_text(symptom_agent).lower():
        return _partial(
            _display_path(symptom_agent),
            "normalization logic exists in symptom agent, but no standalone normalizer module",
            "extract or document entity_normalizer.py",
        )
    return _blocked(_display_path(path), "standalone entity normalization evidence is missing", "implement entity_normalizer.py")


def _gamma_conflict() -> tuple[str, str, str, str]:
    path = ROOT / "agents" / "kg_conflict_agent.py"
    test_path = ROOT / "tests" / "test_kg_conflict.py"
    text = _read_text(path)
    if "compute_conflict_gate" in text and "gamma_conflict" in text and _exists(test_path):
        return _ready(f"{_display_path(path)}, {_display_path(test_path)}", "gamma_conflict computation and tests exist")
    return _blocked(_display_path(path), "gamma_conflict computation is missing", "implement and test KG gate")


def _conflict_injection() -> tuple[str, str, str, str]:
    path = ROOT / "experiments" / "inject_conflicts.py"
    csv_path = ROOT / "experiments" / "results" / "conflict_detection.csv"
    if _exists(path) and _row_status_from_csv(csv_path, min_rows=5):
        return _ready(f"{_display_path(path)}, {_display_path(csv_path)}", "conflict injection script and CSV exist")
    if _row_status_from_csv(csv_path, min_rows=5):
        return _partial(
            _display_path(csv_path),
            "conflict outcomes exist, but there is no standalone inject_conflicts.py script",
            "factor synthetic conflict construction into inject_conflicts.py",
        )
    return _blocked(_display_path(path), "conflict injection evidence is missing", "add conflict injection script")


def _b0_b2_comparison() -> tuple[str, str, str, str]:
    rows = _csv_rows(ROOT / "experiments" / "results" / "conflict_detection.csv")
    by_baseline = {row.get("baseline"): row for row in rows}
    try:
        b0 = float(by_baseline["B0"]["f1"])
        b2 = float(by_baseline["B2"]["f1"])
    except Exception:  # noqa: BLE001
        return _blocked("conflict_detection.csv", "B0/B2 F1 rows are missing", "rerun conflict ablation")
    if b2 > b0:
        return _partial(
            f"conflict_detection.csv; B0_F1={b0:.4f}; B2_F1={b2:.4f}",
            "B2 improves F1 over B0, but no KG gate AUC table is present",
            "add kg_gate_auc.csv or report why AUC is out of scope",
        )
    return _blocked("conflict_detection.csv", "B2 does not improve over B0", "debug KG-gated baseline")


def _extended_skills() -> tuple[str, str, str, str]:
    candidates = [
        REPO_ROOT / "franka_api_server" / "franka_api_server" / "skills" / "poses.yaml",
        REPO_ROOT / "franka_api_server" / "franka_api_server" / "services" / "skills_loader.py",
        REPO_ROOT / "franka_api_server" / "config" / "poses.yaml",
    ]
    text = "\n".join(_read_text(path) for path in candidates)
    planned = ["resample_tongue_left", "resample_tongue_right", "go_to_inspection_home"]
    found = [skill for skill in planned if skill in text]
    if len(found) == len(planned):
        return _ready("poses.yaml", "planned resample skills are configured")
    if "go_to_tongue_pose" in text:
        return _partial(
            "poses.yaml",
            "existing tongue/face skills are present, but planned resample skills are not configured",
            "add and validate fake-hardware resample skills",
        )
    return _blocked("poses.yaml", "skill pose configuration was not found", "locate or restore skill configuration")


def _action_agent() -> tuple[str, str, str, str]:
    path = ROOT / "agents" / "action_agent.py"
    test_path = ROOT / "tests" / "test_pipeline.py"
    if "execute_skill" in _read_text(path) and _exists(test_path):
        return _ready(f"{_display_path(path)}, {_display_path(test_path)}", "Action Agent selects tool calls in low-quality cases")
    return _blocked(_display_path(path), "Action Agent tool-selection evidence is missing", "implement tool selection")


def _closed_loop_script() -> tuple[str, str, str, str]:
    script = REPO_ROOT / "scripts" / "paper2_closed_loop.sh"
    rows = _jsonl_count(ROOT / "experiments" / "logs" / "paper2_run_001.jsonl")
    if _exists(script) and rows >= 10:
        return _ready(f"{_display_path(script)}; jsonl_rows={rows}", "Paper II closed-loop script generates JSONL evidence")
    return _blocked(_display_path(script), "Paper II closed-loop script or JSONL evidence is missing", "run the closed-loop script")


def _latency_summary() -> tuple[str, str, str, str]:
    csv_path = ROOT / "experiments" / "results" / "closed_loop_latency.csv"
    summarize = ROOT / "experiments" / "summarize_closed_loop.py"
    summary_path = ROOT / "experiments" / "results" / "closed_loop_summary.csv"
    rows = len(_csv_rows(csv_path))
    summary_rows = _csv_rows(summary_path)
    has_percentiles = any(
        row.get("latency_p50_ms") not in (None, "")
        and row.get("latency_p95_ms") not in (None, "")
        for row in summary_rows
    )
    if _exists(summarize) and rows >= 10 and has_percentiles:
        return _ready(
            f"{_display_path(summarize)}, {_display_path(summary_path)}; rows={rows}; summary_rows={len(summary_rows)}",
            "M6-style latency summarizer reports p50/p95 and route distribution",
        )
    if _exists(summarize) and rows >= 10:
        return _partial(
            f"{_display_path(summarize)}, {_display_path(csv_path)}; rows={rows}",
            "summarizer script exists, but p50/p95 summary CSV has not been generated",
            "run summarize_closed_loop.py after closed-loop experiments",
        )
    if rows >= 10:
        return _partial(
            f"{_display_path(csv_path)}; rows={rows}",
            "closed-loop latency CSV exists, but no standalone M6-style summarizer is present",
            "add summarize_closed_loop.py with p50/p95 reporting",
        )
    return _blocked(_display_path(csv_path), "closed-loop latency evidence is missing", "rerun closed-loop experiments")


def _safe_exit() -> tuple[str, str, str, str]:
    text = _read_text(ROOT / "langgraph_router" / "routing.py")
    if "retry_count" in text and "human_review" in text and "fail_safe" in text:
        return _ready("routing.py", "retry-based human_review/fail_safe routing is implemented")
    return _blocked("routing.py", "retry/fail-safe routing is missing", "add retry cap and fail-safe tests")


def _emr_schema() -> tuple[str, str, str, str]:
    path = ROOT / "schemas" / "emr_draft.schema.json"
    if _exists(path):
        return _ready(_display_path(path), "EMR draft JSON schema exists")
    return _blocked(_display_path(path), "EMR draft schema is missing", "add schema")


def _fhir_mapping() -> tuple[str, str, str, str]:
    path = ROOT / "agents" / "emr_fhir_agent.py"
    text = _read_text(path)
    if "Composition" in text and "Observation" in text and "Patient" in text:
        return _ready(_display_path(path), "EMR/FHIR agent builds minimal document Bundle resources")
    return _blocked(_display_path(path), "FHIR mapping MVP is missing", "implement Bundle/Composition/Observation mapping")


def _fhir_validator_wrapper() -> tuple[str, str, str, str]:
    path = ROOT / "tools" / "fhir_validator.py"
    test_path = ROOT / "tests" / "test_fhir_validator.py"
    if _exists(path) and _exists(test_path):
        return _ready(f"{_display_path(path)}, {_display_path(test_path)}", "FHIR validator wrapper and tests exist")
    return _blocked(_display_path(path), "FHIR validator wrapper evidence is missing", "add validator wrapper/tests")


def _repair_loop() -> tuple[str, str, str, str]:
    path = ROOT / "agents" / "emr_fhir_agent.py"
    rows = _csv_rows(ROOT / "experiments" / "results" / "fhir_validation.csv")
    by_baseline = {row.get("baseline"): row for row in rows}
    try:
        b2 = float(by_baseline["B2"]["fhir_valid_rate"])
        b4 = float(by_baseline["B4"]["fhir_valid_rate"])
    except Exception:  # noqa: BLE001
        return _blocked("fhir_validation.csv", "B2/B4 FHIR valid-rate rows are missing", "rerun FHIR experiments")
    if "repair_fhir" in _read_text(path) and b4 > b2:
        return _ready(f"{_display_path(path)}; B2={b2:.4f}; B4={b4:.4f}", "repair loop improves FHIR validity")
    return _partial(
        f"{_display_path(path)}; B2={b2:.4f}; B4={b4:.4f}",
        "FHIR evidence exists, but repair-loop improvement is incomplete",
        "debug repair_fhir behavior and rerun B4",
    )


def _sanitized_samples() -> tuple[str, str, str, str]:
    sample = ROOT / "experiments" / "samples" / "paper2_run_001.sample.jsonl"
    dataset = ROOT / "datasets" / "samples" / "paper2_cases.sample.csv"
    if _exists(sample) and _exists(dataset):
        return _ready(f"{_display_path(sample)}, {_display_path(dataset)}", "tracked samples are synthetic/no-PHI artifacts")
    return _blocked(_display_path(sample), "sanitized sample evidence is missing", "add no-PHI samples")


def _b0_b4_experiment() -> tuple[str, str, str, str]:
    rows = _csv_rows(ROOT / "experiments" / "results" / "paper2_summary.csv")
    baselines = {row.get("baseline") for row in rows}
    if {"B0", "B1", "B2", "B3", "B4"} <= baselines:
        return _partial(
            f"paper2_summary.csv; baselines={len(baselines)}",
            "B0-B4 results exist for one deterministic synthetic run, but not 3 seeds",
            "add multi-seed experiment matrix",
        )
    return _blocked("paper2_summary.csv", "B0-B4 result rows are incomplete", "rerun baseline experiment")


def _tool_ablation() -> tuple[str, str, str, str]:
    path = ROOT / "experiments" / "results" / "tool_ablation.csv"
    if _row_status_from_csv(path, min_rows=5):
        return _ready(_display_path(path), "tool-call effectiveness table exists")
    return _blocked(_display_path(path), "tool ablation table is missing", "rerun tool ablation")


def _hallucination_eval() -> tuple[str, str, str, str]:
    path = ROOT / "experiments" / "results" / "hallucination_eval.csv"
    summary = ROOT / "experiments" / "results" / "paper2_summary.csv"
    if _row_status_from_csv(path, min_rows=1):
        return _ready(_display_path(path), "standalone hallucination evaluation table exists")
    if _row_status_from_csv(summary, min_rows=5):
        return _partial(
            _display_path(summary),
            "hallucination rates are in summary CSV, but standalone hallucination_eval.csv is missing",
            "export hallucination_eval.csv with fixed annotation rules",
        )
    return _blocked(_display_path(path), "hallucination evaluation evidence is missing", "add hallucination evaluation")


def _figures() -> tuple[str, str, str, str]:
    path = ROOT / "figures" / "plot_results.py"
    svg = ROOT / "figures" / "paper2_summary_metrics.svg"
    if _exists(path) and _exists(svg):
        return _ready(f"{_display_path(path)}, {_display_path(svg)}", "figure script and rendered figures exist")
    return _blocked(_display_path(path), "figure generation evidence is missing", "run plot_results.py")


def _results_section() -> tuple[str, str, str, str]:
    section = ROOT / "latex" / "sections" / "results.tex"
    main = ROOT / "latex" / "main.tex"
    if _exists(section):
        return _ready(_display_path(section), "standalone results section exists")
    if "Paper II MVP results" in _read_text(main):
        return _partial(
            _display_path(main),
            "results are present in monolithic LaTeX, but latex/sections/results.tex is missing",
            "split manuscript into section files before submission",
        )
    return _blocked(_display_path(section), "results section text is missing", "write results section")


def _method_section() -> tuple[str, str, str, str]:
    section = ROOT / "latex" / "sections" / "method.tex"
    main = ROOT / "latex" / "main.tex"
    if _exists(section):
        return _ready(_display_path(section), "standalone method section exists")
    if "KG gate" in _read_text(main):
        return _partial(_display_path(main), "method content exists in monolithic LaTeX", "split method.tex")
    return _blocked(_display_path(section), "method section is missing", "write method section")


def _system_section() -> tuple[str, str, str, str]:
    section = ROOT / "latex" / "sections" / "system.tex"
    main = ROOT / "latex" / "main.tex"
    if _exists(section):
        return _ready(_display_path(section), "standalone system section exists")
    if "franka_api_server" in _read_text(main):
        return _partial(_display_path(main), "system boundary exists in monolithic LaTeX", "split system.tex")
    return _blocked(_display_path(section), "system section is missing", "write system section")


def _patent_disclosure() -> tuple[str, str, str, str]:
    path = ROOT / "patent" / "paper2_disclosure.md"
    if _exists(path):
        return _ready(_display_path(path), "Paper II patent disclosure exists")
    return _blocked(_display_path(path), "Paper II patent disclosure is missing", "draft conflict-gating/self-healing disclosure")


def _reproduce_doc() -> tuple[str, str, str, str]:
    path = ROOT / "REPRODUCE.md"
    if _exists(path) and "python3 -m pytest doctor/paper2/tests -q" in _read_text(path):
        return _ready(_display_path(path), "third-party synthetic MVP reproduction instructions exist")
    return _blocked(_display_path(path), "reproduction instructions are missing", "write REPRODUCE.md")


def _submission_route() -> tuple[str, str, str, str]:
    docs = [ROOT / "REPRODUCE.md", REPO_ROOT / "docs-zh" / "paper2" / "论文II_中文稿_20260531.md"]
    joined = "\n".join(_read_text(path) for path in docs)
    if "submission-ready" in joined and "credentialing" in joined and "official" in joined:
        return _partial(
            "REPRODUCE.md, bilingual drafts",
            "submission blockers are documented, but no target journal/ethics checklist is finalized",
            "add target journal and ethics/data-license checklist",
        )
    return _blocked("submission checklist", "submission route review is missing", "write target journal and ethics checklist")


TASKS: list[PhaseTask] = [
    PhaseTask("P2-0", "P2-0-1", "固化本方案与 README", False, _plan_and_docs),
    PhaseTask("P2-0", "P2-0-2", "记录 GitNexus 状态", False, _gitnexus_status_recorded),
    PhaseTask("P2-0", "P2-0-3", "复核论文 I 当前闭环", False, _paper1_loop_reviewed),
    PhaseTask("P2-0", "P2-0-4", "确定 doctor/paper2 纳入本仓", False, _paper2_directory_strategy),
    PhaseTask("P2-0", "P2-0-5", "建立 secrets 规则", True, _secrets_rule),
    PhaseTask("P2-1", "P2-1-1", "新建 doctor/paper2 骨架", False, _skeleton_tests),
    PhaseTask("P2-1", "P2-1-2", "定义 Paper2State", False, _state_object),
    PhaseTask("P2-1", "P2-1-3", "实现规则路由", False, _routing_rules),
    PhaseTask("P2-1", "P2-1-4", "实现单 trial runner", False, _runner_jsonl),
    PhaseTask("P2-1", "P2-1-5", "复用 franka client", False, _franka_client),
    PhaseTask("P2-2", "P2-2-1", "小型 KG schema", True, _kg_schema),
    PhaseTask("P2-2", "P2-2-2", "实体归一化", True, _entity_normalizer),
    PhaseTask("P2-2", "P2-2-3", "gamma_conflict 计算", False, _gamma_conflict),
    PhaseTask("P2-2", "P2-2-4", "冲突注入脚本", False, _conflict_injection),
    PhaseTask("P2-2", "P2-2-5", "B0/B1/B2 对比", False, _b0_b2_comparison),
    PhaseTask("P2-3", "P2-3-1", "扩展 Skills 清单", True, _extended_skills),
    PhaseTask("P2-3", "P2-3-2", "Action Agent 工具选择", False, _action_agent),
    PhaseTask("P2-3", "P2-3-3", "closed-loop 脚本", False, _closed_loop_script),
    PhaseTask("P2-3", "P2-3-4", "M6 风格 RTT 汇总", False, _latency_summary),
    PhaseTask("P2-3", "P2-3-5", "安全退出", True, _safe_exit),
    PhaseTask("P2-4", "P2-4-1", "EMR draft schema", False, _emr_schema),
    PhaseTask("P2-4", "P2-4-2", "FHIR mapping MVP", False, _fhir_mapping),
    PhaseTask("P2-4", "P2-4-3", "FHIR validator wrapper", True, _fhir_validator_wrapper),
    PhaseTask("P2-4", "P2-4-4", "repair loop", False, _repair_loop),
    PhaseTask("P2-4", "P2-4-5", "输出脱敏样例", True, _sanitized_samples),
    PhaseTask("P2-5", "P2-5-1", "B0-B4 全量实验", False, _b0_b4_experiment),
    PhaseTask("P2-5", "P2-5-2", "工具调用有效性统计", False, _tool_ablation),
    PhaseTask("P2-5", "P2-5-3", "幻觉率评估", False, _hallucination_eval),
    PhaseTask("P2-5", "P2-5-4", "图表脚本", False, _figures),
    PhaseTask("P2-5", "P2-5-5", "初稿结果段", False, _results_section),
    PhaseTask("P2-6", "P2-6-1", "方法章节初稿", False, _method_section),
    PhaseTask("P2-6", "P2-6-2", "系统章节", False, _system_section),
    PhaseTask("P2-6", "P2-6-3", "专利交底", False, _patent_disclosure),
    PhaseTask("P2-6", "P2-6-4", "复现实验说明", False, _reproduce_doc),
    PhaseTask("P2-6", "P2-6-5", "投稿路线复核", True, _submission_route),
]


def build_rows() -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    for task in TASKS:
        status, evidence, reason, next_action = task.evaluator()
        if status not in VALID_STATUSES:
            raise ValueError(f"invalid status for {task.task_id}: {status}")
        rows.append(
            {
                "phase": task.phase,
                "task_id": task.task_id,
                "task": task.task,
                "status": status,
                "required_for_submission": "true" if task.required_for_submission else "false",
                "evidence": evidence,
                "reason": reason,
                "next_action": next_action,
            }
        )
    return rows


def _write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def validate_phase_completion_audit_csv(path: Path = DEFAULT_OUT) -> PhaseAuditValidation:
    if not path.is_file():
        return PhaseAuditValidation(False, 0, 0, 0, 0, 0, f"phase audit CSV not found: {path}")
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            return PhaseAuditValidation(
                False,
                0,
                0,
                0,
                0,
                0,
                f"missing column(s): {', '.join(sorted(missing))}",
            )
        rows = list(reader)
    counts = Counter(row.get("status", "") for row in rows)
    phases = {row.get("phase", "") for row in rows if row.get("phase")}
    blocked_required = [
        row["task_id"]
        for row in rows
        if row.get("required_for_submission") == "true" and row.get("status") == STATUS_BLOCKED
    ]
    ready = bool(rows) and not blocked_required
    reason = (
        "no submission-required phase tasks are blocked"
        if ready
        else f"blocked submission-required task(s): {', '.join(blocked_required)}"
    )
    return PhaseAuditValidation(
        ready,
        len(rows),
        counts[STATUS_READY],
        counts[STATUS_PARTIAL],
        counts[STATUS_BLOCKED],
        len(phases),
        reason,
    )


def _write_report(path: Path, rows: list[dict[str, str]], validation: PhaseAuditValidation) -> None:
    by_phase: dict[str, Counter[str]] = defaultdict(Counter)
    for row in rows:
        by_phase[row["phase"]][row["status"]] += 1

    lines = [
        "# Paper II Phase Completion Audit Report",
        "",
        "Conservative task-by-task evidence map for the P2-0..P2-6 work plan.",
        "",
        f"- rows: {validation.rows}",
        f"- phases: {validation.phases}",
        f"- ready: {validation.ready_rows}",
        f"- partial: {validation.partial_rows}",
        f"- blocked: {validation.blocked_rows}",
        f"- no submission-required phase task blocked: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Phase | Ready | Partial | Blocked |",
        "|---|---:|---:|---:|",
    ]
    for phase in sorted(by_phase):
        counts = by_phase[phase]
        lines.append(
            f"| {phase} | {counts[STATUS_READY]} | {counts[STATUS_PARTIAL]} | {counts[STATUS_BLOCKED]} |"
        )

    lines.extend(
        [
            "",
            "| Phase | Task | Status | Required | Evidence | Reason | Next Action |",
            "|---|---|---|---:|---|---|---|",
        ]
    )
    for row in rows:
        lines.append(
            f"| {row['phase']} | {row['task_id']} {row['task']} | {row['status']} | "
            f"{'yes' if row['required_for_submission'] == 'true' else 'no'} | "
            f"{row['evidence']} | {row['reason']} | {row['next_action']} |"
        )
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> PhaseAuditValidation:
    rows = build_rows()
    _write_csv(out_path, rows)
    validation = validate_phase_completion_audit_csv(out_path)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()
    validation = run(out_path=args.out, report_path=args.report)
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
