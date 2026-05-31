"""Audit Chinese/English Paper II manuscript evidence synchronization.

The audit is deliberately mechanical. It checks whether both language drafts
and their LaTeX sources mention the same key evidence, limitations, and gate
counts, then records a conservative CSV/Markdown report for readiness gating.
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parents[1]
DEFAULT_ZH_MD = REPO_ROOT / "docs-zh" / "paper2" / "论文II_中文稿_20260531.md"
DEFAULT_EN_MD = REPO_ROOT / "docs-zh" / "paper2" / "PaperII_English_Draft_20260531.md"
DEFAULT_ZH_TEX = ROOT / "latex" / "main-zh.tex"
DEFAULT_EN_TEX = ROOT / "latex" / "main.tex"
DEFAULT_ZH_PDF = ROOT / "latex" / "main-zh.pdf"
DEFAULT_EN_PDF = ROOT / "latex" / "main.pdf"
DEFAULT_OUT = ROOT / "experiments" / "results" / "bilingual_sync_audit.csv"
DEFAULT_REPORT = ROOT / "experiments" / "reports" / "bilingual_sync_audit_report.md"

STATUS_READY = "ready"
STATUS_BLOCKED = "blocked"

AUDIT_FIELDNAMES = [
    "record_type",
    "concept_id",
    "status",
    "zh_hit",
    "en_hit",
    "zh_artifact",
    "en_artifact",
    "evidence",
    "reason",
    "next_action",
]


@dataclass(frozen=True)
class ConceptSpec:
    concept_id: str
    zh_pattern: str
    en_pattern: str
    zh_example: str
    en_example: str
    required_in_latex: bool = False


@dataclass(frozen=True)
class BilingualSyncAuditValidation:
    ready: bool
    rows: int
    ready_rows: int
    blocked_rows: int
    concept_rows: int
    reason: str


REQUIRED_CONCEPTS = [
    ConceptSpec(
        "synthetic_mvp_scope",
        r"24\s*(?:个\s*)?(?:synthetic\s*)?trial",
        r"24\s+synthetic\s+trials?",
        "24 个 synthetic trial",
        "24 synthetic trials",
        True,
    ),
    ConceptSpec(
        "jsonl_audit_records",
        r"120.{0,40}JSONL",
        r"120.{0,40}JSONL",
        "120 行 JSONL 审计轨迹",
        "120 JSONL audit records",
    ),
    ConceptSpec(
        "b0_conflict_f1",
        r"B0.{0,100}F1.{0,30}0\.7500",
        r"B0.{0,100}F1.{0,30}0\.7500",
        "B0 的冲突检出 F1 为 0.7500",
        "B0 obtains a conflict-detection F1 of 0.7500",
        True,
    ),
    ConceptSpec(
        "b0_hallucination_rate",
        r"B0.{0,120}幻觉率.{0,30}0\.6250",
        r"B0.{0,120}hallucination rate.{0,30}0\.6250",
        "B0 的幻觉率为 0.6250",
        "B0 obtains a hallucination rate of 0.6250",
        True,
    ),
    ConceptSpec(
        "b2_conflict_f1",
        r"B2.{0,100}F1.{0,30}1\.0000",
        r"B2.{0,100}F1.{0,30}1\.0000",
        "B2 的冲突检出 F1 达到 1.0000",
        "B2 reaches an F1 of 1.0000",
        True,
    ),
    ConceptSpec(
        "b2_hallucination_rate",
        r"B2.{0,120}幻觉率.{0,30}0\.0000",
        r"B2.{0,120}hallucination rate.{0,30}0\.0000",
        "B2 的幻觉率降至 0.0000",
        "B2 reduces hallucination rate to 0.0000",
        True,
    ),
    ConceptSpec(
        "b4_fhir_valid_rate",
        r"B4.{0,120}FHIR.{0,40}(?:有效率|valid rate).{0,30}0\.6250",
        r"B4.{0,120}FHIR valid rate.{0,30}0\.6250",
        "B4 将 FHIR 有效率提升至 0.6250",
        "B4 improves the FHIR valid rate to 0.6250",
        True,
    ),
    ConceptSpec(
        "sample_dataset_replay",
        r"sample_open_csv",
        r"sample_open_csv",
        "sample_open_csv no-PHI fixture",
        "sample_open_csv fixture",
    ),
    ConceptSpec(
        "dataset_compliance_audit",
        r"dataset_compliance_audit",
        r"dataset_compliance_audit",
        "dataset_compliance_audit",
        "dataset_compliance_audit",
    ),
    ConceptSpec(
        "entity_map_placeholder",
        r"placeholder-only",
        r"placeholder-only",
        "placeholder-only",
        "placeholder-only",
        True,
    ),
    ConceptSpec(
        "licensed_ontology_identifier_audit",
        r"run_ontology_identifier_audit\.py|licensed_ontology_identifiers\.template\.csv|授权本体标识审计",
        r"run_ontology_identifier_audit\.py|licensed_ontology_identifiers\.template\.csv|licensed-ontology identifier audit|licensed ontology identifier audit",
        "run_ontology_identifier_audit.py 会输出 licensed_ontology_identifiers.template.csv",
        "run_ontology_identifier_audit.py writes licensed_ontology_identifiers.template.csv",
    ),
    ConceptSpec(
        "graph_attention_lite",
        r"graph-attention-lite",
        r"graph-attention-lite",
        "graph-attention-lite",
        "graph-attention-lite",
        True,
    ),
    ConceptSpec(
        "large_gnn_evidence_audit",
        r"run_large_gnn_evidence_audit\.py|large_gnn_evidence\.template\.csv|大图 GNN/GAT 证据审计",
        r"run_large_gnn_evidence_audit\.py|large_gnn_evidence\.template\.csv|large-GNN evidence audit|large GNN/GAT evidence audit",
        "run_large_gnn_evidence_audit.py 会输出 large_gnn_evidence.template.csv",
        "run_large_gnn_evidence_audit.py writes large_gnn_evidence.template.csv",
        True,
    ),
    ConceptSpec(
        "fhir_validator_replay",
        r"FHIR validator replay.{0,160}120|120.{0,100}Bundle",
        r"FHIR validator replay.{0,160}120|120.{0,100}Bundle",
        "FHIR validator replay 导出 120 个 Bundle JSON",
        "FHIR validator replay exports 120 Bundle JSON artifacts",
    ),
    ConceptSpec(
        "official_fhir_validator_blocked",
        r"official-validator audit.{0,200}blocked|官方.{0,40}validator.{0,200}blocked|official_fhir_validator_audit",
        r"official-validator audit.{0,200}blocked|official FHIR validator.{0,200}blocked|official_fhir_validator_audit",
        "official-validator audit 在默认离线运行中保持 blocked",
        "official-validator audit is blocked in the default offline run",
        True,
    ),
    ConceptSpec(
        "real_expert_review_gate",
        r"real_annotations\.template\.csv|run_real_expert_review\.py",
        r"real_annotations\.template\.csv|run_real_expert_review\.py",
        "run_real_expert_review.py 输出 real_annotations.template.csv",
        "run_real_expert_review.py writes real_annotations.template.csv",
    ),
    ConceptSpec(
        "franka_closed_loop_gate",
        r"run_franka_closed_loop\.py|franka_closed_loop\.csv|Franka API/Gazebo/FR3",
        r"run_franka_closed_loop\.py|franka_closed_loop\.csv|Franka API/Gazebo/FR3",
        "Franka API/Gazebo/FR3 闭环证据",
        "Franka API/Gazebo/FR3 closed-loop evidence",
    ),
    ConceptSpec(
        "closed_loop_summary",
        r"closed_loop_summary|闭环(?:延迟|时延)汇总|latency p50",
        r"closed_loop_summary|closed-loop latency summary|latency p50",
        "closed_loop_summary 汇总 synthetic 本地闭环时延",
        "closed_loop_summary latency summary reports synthetic local timing",
        True,
    ),
    ConceptSpec(
        "readiness_counts",
        r"18.{0,80}gate.{0,80}ready.{0,20}8.{0,40}partial.{0,20}1.{0,40}blocked.{0,20}9|18\s*个\s*gate.{0,80}ready\s*8\s*个.{0,40}partial\s*1\s*个.{0,40}blocked\s*9\s*个",
        r"8\s+of\s+18\s+gates\s+are\s+ready.{0,80}1\s+is\s+partial.{0,80}9\s+are\s+blocked|18\s+gates.{0,80}ready\s+8.{0,40}partial\s+1.{0,40}blocked\s+9",
        "18 个 gate 中 ready 8 个、partial 1 个、blocked 9 个",
        "8 of 18 gates are ready, 1 is partial, and 9 are blocked",
        True,
    ),
    ConceptSpec(
        "required_gate_counts",
        r"3/13\s*ready",
        r"3\s+of\s+13\s+submission-required\s+gates\s+are\s+ready|3/13\s*ready",
        "投稿必需 gate 为 3/13 ready",
        "3 of 13 submission-required gates are ready",
    ),
    ConceptSpec(
        "submission_ready_no",
        r"submission-ready.{0,40}no",
        r"submission-ready.{0,40}no",
        "submission-ready 为 no",
        "submission-ready is no",
        True,
    ),
    ConceptSpec(
        "no_clinical_validation",
        r"不构成临床验证|不能作为.{0,40}临床",
        r"not clinical validation|not.{0,80}clinical validation",
        "不构成临床验证",
        "not clinical validation",
        True,
    ),
    ConceptSpec(
        "bilingual_sync_audit",
        r"bilingual_sync_audit|双语(?:论文)?同步审计",
        r"bilingual_sync_audit|bilingual (?:manuscript )?sync audit|bilingual (?:manuscript )?synchronization audit",
        "双语同步审计 bilingual_sync_audit",
        "bilingual_sync_audit bilingual sync audit",
        True,
    ),
    ConceptSpec(
        "phase_completion_audit",
        r"phase_completion_audit|阶段(?:任务)?完成度审计|35\s*项(?:阶段)?任务",
        r"phase_completion_audit|phase completion audit|35\s+planned phase tasks",
        "phase_completion_audit 阶段完成度审计，35 项任务",
        "phase_completion_audit phase completion audit over 35 planned phase tasks",
        True,
    ),
]


def _display_path(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(REPO_ROOT.resolve()))
    except ValueError:
        return str(path)


def _normalize_text(text: str) -> str:
    text = text.replace("\\_", "_")
    text = text.replace("\u3000", " ")
    return re.sub(r"\s+", " ", text)


def _read_text(path: Path) -> str:
    if not path.is_file():
        return ""
    return _normalize_text(path.read_text(encoding="utf-8"))


def _has_match(pattern: str, text: str) -> bool:
    return bool(text and re.search(pattern, text, flags=re.IGNORECASE | re.DOTALL))


def _artifact_ready(path: Path) -> bool:
    return path.is_file() and path.stat().st_size > 0


def _paired_artifact_row(
    record_type: str,
    concept_id: str,
    zh_path: Path,
    en_path: Path,
    *,
    zh_source_path: Path | None = None,
    en_source_path: Path | None = None,
) -> dict[str, Any]:
    zh_ready = _artifact_ready(zh_path)
    en_ready = _artifact_ready(en_path)
    stale: list[str] = []
    if zh_ready and zh_source_path and zh_source_path.is_file():
        if zh_path.stat().st_mtime + 1.0 < zh_source_path.stat().st_mtime:
            stale.append(f"{_display_path(zh_path)} older than {_display_path(zh_source_path)}")
    if en_ready and en_source_path and en_source_path.is_file():
        if en_path.stat().st_mtime + 1.0 < en_source_path.stat().st_mtime:
            stale.append(f"{_display_path(en_path)} older than {_display_path(en_source_path)}")
    status = STATUS_READY if zh_ready and en_ready and not stale else STATUS_BLOCKED
    missing = [
        _display_path(path)
        for path, ready in ((zh_path, zh_ready), (en_path, en_ready))
        if not ready
    ]
    issue = "missing/empty: " + ", ".join(missing) if missing else "stale artifact(s): " + "; ".join(stale)
    return {
        "record_type": record_type,
        "concept_id": concept_id,
        "status": status,
        "zh_hit": zh_ready,
        "en_hit": en_ready,
        "zh_artifact": _display_path(zh_path),
        "en_artifact": _display_path(en_path),
        "evidence": "non-empty paired artifact files",
        "reason": "paired artifacts exist and are current" if status == STATUS_READY else issue,
        "next_action": (
            "keep both artifacts regenerated after manuscript edits"
            if status == STATUS_READY
            else "create or regenerate the missing language artifact"
        ),
    }


def _concept_row(
    record_type: str,
    concept: ConceptSpec,
    *,
    zh_text: str,
    en_text: str,
    zh_path: Path,
    en_path: Path,
) -> dict[str, Any]:
    zh_hit = _has_match(concept.zh_pattern, zh_text)
    en_hit = _has_match(concept.en_pattern, en_text)
    status = STATUS_READY if zh_hit and en_hit else STATUS_BLOCKED
    missing = []
    if not zh_hit:
        missing.append("zh")
    if not en_hit:
        missing.append("en")
    return {
        "record_type": record_type,
        "concept_id": concept.concept_id,
        "status": status,
        "zh_hit": zh_hit,
        "en_hit": en_hit,
        "zh_artifact": _display_path(zh_path),
        "en_artifact": _display_path(en_path),
        "evidence": f"zh: {concept.zh_example}; en: {concept.en_example}",
        "reason": (
            "concept appears in both language artifacts"
            if status == STATUS_READY
            else f"concept missing from {', '.join(missing)} artifact(s)"
        ),
        "next_action": (
            "keep this evidence synchronized in both language versions"
            if status == STATUS_READY
            else "update the missing language version with the same evidence and limitation"
        ),
    }


def _write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=AUDIT_FIELDNAMES, lineterminator="\n")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in AUDIT_FIELDNAMES})


def validate_bilingual_sync_audit_csv(path: Path = DEFAULT_OUT) -> BilingualSyncAuditValidation:
    if not path.is_file():
        return BilingualSyncAuditValidation(
            False,
            0,
            0,
            0,
            0,
            f"bilingual sync audit CSV not found: {path}",
        )
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        missing = set(AUDIT_FIELDNAMES) - set(reader.fieldnames or [])
        if missing:
            return BilingualSyncAuditValidation(
                False,
                0,
                0,
                0,
                0,
                f"missing column(s): {', '.join(sorted(missing))}",
            )
        rows = list(reader)

    ready_rows = [row for row in rows if row.get("status") == STATUS_READY]
    blocked_rows = [row for row in rows if row.get("status") != STATUS_READY]
    concept_rows = [row for row in rows if row.get("record_type", "").endswith("_concept")]
    if rows and not blocked_rows:
        reason = f"{len(concept_rows)} bilingual concept row(s) passed audit"
        ready = True
    else:
        reasons = [row.get("reason", "") for row in blocked_rows if row.get("reason")]
        reason = "; ".join(reasons[:5]) or "bilingual manuscript synchronization evidence is incomplete"
        ready = False
    return BilingualSyncAuditValidation(
        ready,
        len(rows),
        len(ready_rows),
        len(blocked_rows),
        len(concept_rows),
        reason,
    )


def _write_report(
    report_path: Path,
    rows: list[dict[str, Any]],
    validation: BilingualSyncAuditValidation,
) -> None:
    lines = [
        "# Bilingual Sync Audit Report",
        "",
        "Conservative audit for Chinese/English Paper II manuscript synchronization.",
        "",
        f"- rows: {validation.rows}",
        f"- concept rows: {validation.concept_rows}",
        f"- ready rows: {validation.ready_rows}",
        f"- blocked rows: {validation.blocked_rows}",
        f"- ready: {'yes' if validation.ready else 'no'}",
        f"- reason: {validation.reason}",
        "",
        "| Record | Concept | Status | ZH | EN | Reason |",
        "|---|---|---|---:|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row.get('record_type', '')} | {row.get('concept_id', '')} | "
            f"{row.get('status', '')} | {row.get('zh_hit', '')} | {row.get('en_hit', '')} | "
            f"{row.get('reason', '')} |"
        )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run(
    *,
    zh_md_path: Path = DEFAULT_ZH_MD,
    en_md_path: Path = DEFAULT_EN_MD,
    zh_tex_path: Path = DEFAULT_ZH_TEX,
    en_tex_path: Path = DEFAULT_EN_TEX,
    zh_pdf_path: Path = DEFAULT_ZH_PDF,
    en_pdf_path: Path = DEFAULT_EN_PDF,
    out_path: Path = DEFAULT_OUT,
    report_path: Path = DEFAULT_REPORT,
) -> BilingualSyncAuditValidation:
    zh_md = _read_text(zh_md_path)
    en_md = _read_text(en_md_path)
    zh_tex = _read_text(zh_tex_path)
    en_tex = _read_text(en_tex_path)

    rows = [
        _paired_artifact_row("artifact_pair", "markdown_pair", zh_md_path, en_md_path),
        _paired_artifact_row("artifact_pair", "latex_source_pair", zh_tex_path, en_tex_path),
        _paired_artifact_row(
            "artifact_pair",
            "pdf_pair",
            zh_pdf_path,
            en_pdf_path,
            zh_source_path=zh_tex_path,
            en_source_path=en_tex_path,
        ),
    ]
    for concept in REQUIRED_CONCEPTS:
        rows.append(
            _concept_row(
                "markdown_concept",
                concept,
                zh_text=zh_md,
                en_text=en_md,
                zh_path=zh_md_path,
                en_path=en_md_path,
            )
        )
        if concept.required_in_latex:
            rows.append(
                _concept_row(
                    "latex_concept",
                    concept,
                    zh_text=zh_tex,
                    en_text=en_tex,
                    zh_path=zh_tex_path,
                    en_path=en_tex_path,
                )
            )

    _write_csv(out_path, rows)
    validation = validate_bilingual_sync_audit_csv(out_path)
    _write_report(report_path, rows, validation)
    return validation


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--zh", type=Path, default=DEFAULT_ZH_MD)
    parser.add_argument("--en", type=Path, default=DEFAULT_EN_MD)
    parser.add_argument("--zh-tex", type=Path, default=DEFAULT_ZH_TEX)
    parser.add_argument("--en-tex", type=Path, default=DEFAULT_EN_TEX)
    parser.add_argument("--zh-pdf", type=Path, default=DEFAULT_ZH_PDF)
    parser.add_argument("--en-pdf", type=Path, default=DEFAULT_EN_PDF)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT)
    args = parser.parse_args()

    validation = run(
        zh_md_path=args.zh,
        en_md_path=args.en,
        zh_tex_path=args.zh_tex,
        en_tex_path=args.en_tex,
        zh_pdf_path=args.zh_pdf,
        en_pdf_path=args.en_pdf,
        out_path=args.out,
        report_path=args.report,
    )
    print(json.dumps(validation.__dict__, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
