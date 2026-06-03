#!/usr/bin/env bash
# Run step 6+ pipeline, wait for completion, auto-summarize to docs-zh.
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG="$ROOT/doctor/paper1/experiments/logs/tcm_full_resume.log"
SUMMARY_FLAG="$ROOT/doctor/paper1/experiments/logs/tcm_full_summary.done"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Starting step6 resume pipeline..."
bash "$ROOT/scripts/paper1_run_tcm_full_resume_step6.sh"
ec=$?

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Pipeline exit=$ec, running summarize..."
python3 "$ROOT/scripts/paper1_summarize_full_run.py" | tee -a "$LOG"

{
  echo "================================================================"
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] Auto-summary complete exit=$ec"
  echo "  summary=docs-zh/paper1/论文I_全量验证结果_20260531.md"
  echo "================================================================"
} >>"$LOG"

date '+%Y-%m-%d %H:%M:%S' >"$SUMMARY_FLAG"
exit "$ec"
