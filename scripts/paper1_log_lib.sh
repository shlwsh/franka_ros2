# shellcheck shell=bash
# Paper I pipeline logging: timestamps + step banners (sourced by paper1_run_*.sh)
paper1_log_init() {
  local log_path="${1:-experiments/logs/paper1_pipeline.log}"
  mkdir -p "$(dirname "$log_path")"
  export PAPER1_LOG_FILE="$log_path"
  export PAPER1_LOG_START_TS
  PAPER1_LOG_START_TS="$(date '+%Y-%m-%d %H:%M:%S %z')"
  {
    echo "================================================================"
    echo "[$PAPER1_LOG_START_TS] Paper I pipeline log start"
    echo "  cwd=$(pwd)"
    echo "  host=$(hostname 2>/dev/null || echo unknown)"
    echo "  user=${USER:-unknown}"
    echo "  log_file=$PAPER1_LOG_FILE"
    echo "================================================================"
  } >>"$PAPER1_LOG_FILE"
}

paper1_log_ts() {
  date '+%Y-%m-%d %H:%M:%S'
}

paper1_log_info() {
  local line="[$(paper1_log_ts)] [INFO] $*"
  echo "$line"
  if [[ -n "${PAPER1_LOG_FILE:-}" ]]; then
    echo "$line" >>"$PAPER1_LOG_FILE"
  fi
}

paper1_log_error() {
  local line="[$(paper1_log_ts)] [ERROR] $*"
  echo "$line" >&2
  if [[ -n "${PAPER1_LOG_FILE:-}" ]]; then
    echo "$line" >>"$PAPER1_LOG_FILE"
  fi
}

# Run Python with unbuffered stdout; path must be quoted by caller.
paper1_run_python() {
  local interpreter="$1"
  shift
  local script="$1"
  shift
  paper1_log_info "RUN script=${script} interpreter=${interpreter} args=$*"
  set -o pipefail
  if [[ -n "${PAPER1_LOG_FILE:-}" ]]; then
    PAPER1_TRACE="${PAPER1_TRACE:-1}" \
      "$interpreter" -u "$script" "$@"
    local ec=$?
  else
    PAPER1_TRACE="${PAPER1_TRACE:-1}" \
      "$interpreter" -u "$script" "$@" 2>&1 | tee -a /dev/stderr
    local ec="${PIPESTATUS[0]}"
  fi
  if [[ "$ec" -ne 0 ]]; then
    paper1_log_error "EXIT code=${ec} script=${script}"
    return "$ec"
  fi
  paper1_log_info "DONE script=${script}"
  return 0
}

paper1_run_step() {
  local step_id="$1"
  local title="$2"
  shift 2
  paper1_log_info "===== STEP ${step_id}: ${title} ====="
  if "$@"; then
    paper1_log_info "===== STEP ${step_id} OK ====="
    return 0
  fi
  local ec=$?
  paper1_log_error "===== STEP ${step_id} FAILED exit=${ec} ====="
  return "$ec"
}
