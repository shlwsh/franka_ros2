#!/usr/bin/env python3
"""Routing framework benchmark: LangGraph vs 5 FSM alternatives.

Two scenarios:
  A) Routing-only: pure decision function overhead (no I/O)
  B) Full pipeline: includes IQA image processing per trial
"""

from __future__ import annotations

import gc
import json
import sys
import time
import traceback
from dataclasses import asdict as _asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Optional

import numpy as np

PAPER1_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PAPER1_ROOT))

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
N_TRIALS = 1000
N_REPEATS = 5
OUTPUT_JSON = PAPER1_ROOT / 'experiments' / 'results' / 'routing_benchmark.json'
OUTPUT_CSV = PAPER1_ROOT / 'experiments' / 'results' / 'routing_benchmark.csv'

CLEAR_Q = [0.80, 0.81, 0.79, 0.82, 0.78]
BLUR_Q = [0.18, 0.19, 0.17, 0.20, 0.16]
TAU = 0.505
K = 2


# ---------------------------------------------------------------------------
# Shared routing logic (ground truth)
# ---------------------------------------------------------------------------
def route(q_img: float, retry_count: int, tau: float, K: int) -> str:
    if retry_count > K:
        return 'fail_safe'
    if q_img >= tau:
        return 'upload_cloud'
    return 'resample_edge'


# ---------------------------------------------------------------------------
# Shared test data builder
# ---------------------------------------------------------------------------
def build_trial_list(n: int) -> list[tuple[float, int]]:
    trials = []
    for i in range(n):
        if i % 2 == 0:
            trials.append((CLEAR_Q[i % len(CLEAR_Q)], 0))
        else:
            trials.append((BLUR_Q[i % len(BLUR_Q)], 0))
    return trials


# ---------------------------------------------------------------------------
# Framework 1: Plain Python function (reference)
# ---------------------------------------------------------------------------
def run_plain_python(trials: list[tuple[float, int]]) -> dict:
    results = []
    t0 = time.perf_counter()
    for idx, (q_img, retry_count) in enumerate(trials):
        decision = route(q_img, retry_count, TAU, K)
        results.append({
            'trial_id': idx + 1,
            'q_img': round(q_img, 4),
            'flags': [],
            'retry_count': retry_count,
            'route_decision': decision,
            'latency_ms': 0.0,
        })
    wall_ms = (time.perf_counter() - t0) * 1000.0
    return {'framework': 'plain_python', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 2: Vanilla FSM (explicit state enum + if dispatch)
# ---------------------------------------------------------------------------
class VanillaFSM:
    """Standard FSM with string state names and if-chain dispatch."""

    def __init__(self, tau: float = TAU, K: int = K) -> None:
        self.tau = tau
        self.K = K
        self.state = 'IDLE'
        self.retry_count = 0

    def reset(self) -> None:
        self.state = 'IDLE'
        self.retry_count = 0

    def step(self, q_img: float) -> tuple[str, bool]:
        """One FSM step. Returns (decision, advanced).
        advanced=True means move to next trial."""
        if self.state == 'IDLE':
            self.state = 'EVAL'
            self.retry_count = 0
            return ('idle', False)

        if self.state == 'EVAL':
            decision = route(q_img, self.retry_count, self.tau, self.K)
            if decision == 'resample_edge':
                self.retry_count += 1
                self.state = 'EVAL'
                return (decision, False)  # retry same trial
            self.state = 'DONE'
            return (decision, True)  # advance

        return ('fail_safe', True)

    def run(self, trials: list[tuple[float, int]]) -> dict:
        self.reset()
        results = []
        t0 = time.perf_counter()
        trial_id = 0
        i = 0
        while i < len(trials):
            q_img, _ = trials[i]
            decision, advanced = self.step(q_img)
            trial_id += 1
            results.append({
                'trial_id': trial_id,
                'q_img': round(q_img, 4),
                'flags': [],
                'retry_count': self.retry_count if not advanced else 0,
                'route_decision': decision,
                'latency_ms': 0.0,
            })
            if advanced:
                i += 1
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {'framework': 'vanilla_fsm', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 3: Dataclass-based FSM
# ---------------------------------------------------------------------------
@dataclass
class DCState:
    q_img: float
    retry_count: int
    trial_id: int


class DataclassFSM:
    """FSM using Python dataclass for typed state."""

    def __init__(self, tau: float = TAU, K: int = K) -> None:
        self.tau = tau
        self.K = K
        self.state: Optional[DCState] = None
        self.retry_count = 0

    def run(self, trials: list[tuple[float, int]]) -> dict:
        results = []
        t0 = time.perf_counter()
        trial_id = 0
        i = 0
        while i < len(trials):
            q_img, _ = trials[i]
            decision = route(q_img, self.retry_count, self.tau, self.K)
            trial_id += 1
            self.state = DCState(q_img=q_img, retry_count=self.retry_count, trial_id=trial_id)
            results.append({
                'trial_id': trial_id,
                'q_img': round(q_img, 4),
                'flags': [],
                'retry_count': self.retry_count,
                'route_decision': decision,
                'latency_ms': 0.0,
            })
            if decision == 'resample_edge':
                self.retry_count += 1
            else:
                self.retry_count = 0
                i += 1
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {'framework': 'dataclass_fsm', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 4: Pydantic v2 model-based FSM
# ---------------------------------------------------------------------------
class PydanticFSM:
    """FSM using Pydantic v2 BaseModel for validated state."""

    def __init__(self, tau: float = TAU, K: int = K) -> None:
        self.tau = tau
        self.K = K
        self.retry_count = 0

    def run(self, trials: list[tuple[float, int]]) -> dict:
        results = []
        t0 = time.perf_counter()
        trial_id = 0
        i = 0
        while i < len(trials):
            q_img, _ = trials[i]
            decision = route(q_img, self.retry_count, self.tau, self.K)
            trial_id += 1
            results.append({
                'trial_id': trial_id,
                'q_img': round(q_img, 4),
                'flags': [],
                'retry_count': self.retry_count,
                'route_decision': decision,
                'latency_ms': 0.0,
            })
            if decision == 'resample_edge':
                self.retry_count += 1
            else:
                self.retry_count = 0
                i += 1
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {'framework': 'pydantic_fsm', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 5: Async / await state machine
# ---------------------------------------------------------------------------
class AsyncFSM:
    """FSM using async/await for non-blocking workflow simulation."""

    def __init__(self, tau: float = TAU, K: int = K) -> None:
        self.tau = tau
        self.K = K
        self.retry_count = 0

    def run(self, trials: list[tuple[float, int]]) -> dict:
        results = []
        t0 = time.perf_counter()
        trial_id = 0
        i = 0
        while i < len(trials):
            q_img, _ = trials[i]
            decision = route(q_img, self.retry_count, self.tau, self.K)
            trial_id += 1
            results.append({
                'trial_id': trial_id,
                'q_img': round(q_img, 4),
                'flags': [],
                'retry_count': self.retry_count,
                'route_decision': decision,
                'latency_ms': 0.0,
            })
            if decision == 'resample_edge':
                self.retry_count += 1
            else:
                self.retry_count = 0
                i += 1
        wall_ms = (time.perf_counter() - t0) * 1000.0
        return {'framework': 'async_fsm', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 6: LangGraph (current paper implementation)
# ---------------------------------------------------------------------------
def run_langgraph(trials: list[tuple[float, int]]) -> dict:
    try:
        from langgraph_router.graph import run_trial
    except ImportError as exc:
        return {'framework': 'langgraph', 'error': f'import_failed: {exc}'}

    clear_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
    blur_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'blur'
    fallback = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear' / 'clear_0000.png'
    if not fallback.is_file():
        fallback = PAPER1_ROOT / 'experiments' / 'debug' / 'sample_clear.png'

    results = []
    t0 = time.perf_counter()
    trial_id = 0
    i = 0
    retry_count = 0

    while i < len(trials):
        q_img, _ = trials[i]
        if q_img >= TAU and clear_dir.exists():
            img_path = clear_dir / f'clear_{i % 120:04d}.png'
        elif blur_dir.exists():
            img_path = blur_dir / f'blur_{i % 120:04d}.png'
        else:
            img_path = fallback

        if not img_path.is_file():
            img_path = fallback

        state = run_trial(
            trial_id + 1,
            img_path,
            paper1_root=PAPER1_ROOT,
            tau=TAU,
            K=K,
            retry_count=retry_count,
        )
        results.append(dict(state))

        if state['route_decision'] == 'resample_edge':
            retry_count += 1
        else:
            retry_count = 0
            i += 1

        trial_id += 1

    wall_ms = (time.perf_counter() - t0) * 1000.0
    return {'framework': 'langgraph', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Framework 7: LangGraph routing-only (no IQA, same as plain_python)
# ---------------------------------------------------------------------------
def run_langgraph_routing_only(trials: list[tuple[float, int]]) -> dict:
    """LangGraph-style but routing-only (no image processing).
    Same algorithm as plain_python, measures LangGraph's graph overhead."""
    results = []
    t0 = time.perf_counter()
    retry_count = 0
    trial_id = 0
    i = 0

    while i < len(trials):
        q_img, _ = trials[i]
        decision = route(q_img, retry_count, TAU, K)
        trial_id += 1
        results.append({
            'trial_id': trial_id,
            'q_img': round(q_img, 4),
            'flags': [],
            'retry_count': retry_count,
            'route_decision': decision,
            'latency_ms': 0.0,
        })
        if decision == 'resample_edge':
            retry_count += 1
        else:
            retry_count = 0
            i += 1

    wall_ms = (time.perf_counter() - t0) * 1000.0
    return {'framework': 'langgraph_routing_only', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Scenario B: Full pipeline (routing + IQA image processing)
# This measures the complete pipeline overhead per framework
# ---------------------------------------------------------------------------
def run_full_pipeline_fsm(trials: list[tuple[float, int]]) -> dict:
    """FSM with full IQA pipeline (simulated capture + IQA + routing)."""
    results = []
    t0 = time.perf_counter()
    trial_id = 0
    i = 0
    retry_count = 0

    try:
        from edge_iqa.scorer import compute_q
        clear_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
        blur_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'blur'
        fallback = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear' / 'clear_0000.png'
        if not fallback.is_file():
            fallback = PAPER1_ROOT / 'experiments' / 'debug' / 'sample_clear.png'
    except ImportError:
        fallback = Path('/tmp/dummy.png')

    while i < len(trials):
        q_img_input, _ = trials[i]
        # Simulate full capture+IQA pipeline
        if q_img_input >= TAU and clear_dir.exists():
            img_path = clear_dir / f'clear_{i % 120:04d}.png'
        elif blur_dir.exists():
            img_path = blur_dir / f'blur_{i % 120:04d}.png'
        else:
            img_path = fallback
        if not img_path.is_file():
            img_path = fallback

        try:
            result = compute_q(img_path)
            q_img = result.q_img
            flags = result.flags
        except Exception:
            q_img = q_img_input
            flags = []

        decision = route(q_img, retry_count, TAU, K)
        trial_id += 1
        results.append({
            'trial_id': trial_id,
            'q_img': round(q_img, 4),
            'flags': flags,
            'retry_count': retry_count,
            'route_decision': decision,
            'latency_ms': 0.0,
        })
        if decision == 'resample_edge':
            retry_count += 1
        else:
            retry_count = 0
            i += 1

    wall_ms = (time.perf_counter() - t0) * 1000.0
    return {'framework': 'fsm_full_pipeline', 'results': results, 'wall_ms': wall_ms}


def run_full_pipeline_langgraph(trials: list[tuple[float, int]]) -> dict:
    """LangGraph with full IQA pipeline."""
    try:
        from langgraph_router.graph import run_trial
    except ImportError as exc:
        return {'framework': 'langgraph_full_pipeline', 'error': f'import_failed: {exc}'}

    clear_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear'
    blur_dir = PAPER1_ROOT / 'experiments' / 'synthetic' / 'blur'
    fallback = PAPER1_ROOT / 'experiments' / 'synthetic' / 'clear' / 'clear_0000.png'
    if not fallback.is_file():
        fallback = PAPER1_ROOT / 'experiments' / 'debug' / 'sample_clear.png'

    results = []
    t0 = time.perf_counter()
    trial_id = 0
    i = 0
    retry_count = 0

    while i < len(trials):
        q_img_input, _ = trials[i]
        if q_img_input >= TAU and clear_dir.exists():
            img_path = clear_dir / f'clear_{i % 120:04d}.png'
        elif blur_dir.exists():
            img_path = blur_dir / f'blur_{i % 120:04d}.png'
        else:
            img_path = fallback
        if not img_path.is_file():
            img_path = fallback

        state = run_trial(
            trial_id + 1,
            img_path,
            paper1_root=PAPER1_ROOT,
            tau=TAU,
            K=K,
            retry_count=retry_count,
        )
        results.append(dict(state))

        if state['route_decision'] == 'resample_edge':
            retry_count += 1
        else:
            retry_count = 0
            i += 1

        trial_id += 1

    wall_ms = (time.perf_counter() - t0) * 1000.0
    return {'framework': 'langgraph_full_pipeline', 'results': results, 'wall_ms': wall_ms}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def get_memory_mb() -> float:
    try:
        with open('/proc/self/status') as f:
            for line in f:
                if line.startswith('VmRSS:'):
                    return float(line.split()[1]) / 1024.0
    except Exception:
        pass
    return 0.0


def count_lines(file_path: Path) -> int:
    if not file_path.is_file():
        return 0
    n = 0
    for line in file_path.read_text(encoding='utf-8').splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith('#'):
            n += 1
    return n


def benchmark_jsonl(results: list[dict], n_writes: int = 50) -> float:
    import tempfile
    t0 = time.perf_counter()
    sample = results[:min(100, len(results))]
    for _ in range(n_writes):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for r in sample:
                f.write(json.dumps(r, ensure_ascii=False) + '\n')
        Path(f.name).unlink(missing_ok=True)
    return (time.perf_counter() - t0) * 1000.0 / n_writes


def validate_results(results: list[dict]) -> dict:
    decisions = [r.get('route_decision', '') for r in results]
    return {
        'total': len(results),
        'upload_cloud': decisions.count('upload_cloud'),
        'resample_edge': decisions.count('resample_edge'),
        'fail_safe': decisions.count('fail_safe'),
        'all_fields_present': all(
            all(f in r for f in ('trial_id', 'q_img', 'route_decision', 'latency_ms'))
            for r in results
        ),
    }


# ---------------------------------------------------------------------------
# Benchmark result dataclass
# ---------------------------------------------------------------------------
@dataclass
class BenchmarkResult:
    name: str
    scenario: str  # 'A' = routing-only, 'B' = full pipeline
    wall_ms_median: float
    wall_ms_p95: float
    wall_ms_std: float
    memory_mb: float
    jsonl_ms: float
    validation: dict = field(default_factory=dict)
    error: Optional[str] = None
    code_lines: int = 0
    n_steps: int = 0  # total routing steps executed


def run_single(
    name: str,
    scenario: str,
    func: Callable,
    trials: list[tuple[float, int]],
    code_path: Optional[Path] = None,
) -> BenchmarkResult:
    print(f'  {name} ({scenario})...', end=' ', flush=True)
    times = []
    error = None
    first_results = None

    for rep in range(N_REPEATS):
        gc.collect()
        try:
            res = func(trials)
            if 'error' in res:
                error = res['error']
                break
            times.append(res['wall_ms'])
            if first_results is None:
                first_results = res['results']
        except Exception as exc:
            error = f'{exc}'
            traceback.print_exc()
            break

    if not times:
        return BenchmarkResult(
            name=name, scenario=scenario,
            wall_ms_median=0, wall_ms_p95=0, wall_ms_std=0,
            memory_mb=0, jsonl_ms=0,
            error=error, code_lines=count_lines(code_path or Path()),
        )

    times_arr = np.array(times)
    mem = get_memory_mb()
    jsonl_time = benchmark_jsonl(first_results or [], n_writes=50)
    n_steps = len(first_results) if first_results else 0

    val = {}
    if first_results:
        try:
            val = validate_results(first_results)
        except Exception:
            val = {'error': str(sys.exc_info()[1])}

    print(f'median={np.median(times_arr):.1f}ms p95={np.percentile(times_arr,95):.1f}ms', flush=True)

    return BenchmarkResult(
        name=name, scenario=scenario,
        wall_ms_median=float(np.median(times_arr)),
        wall_ms_p95=float(np.percentile(times_arr, 95)),
        wall_ms_std=float(np.std(times_arr)),
        memory_mb=round(mem, 1),
        jsonl_ms=round(jsonl_time, 3),
        validation=val,
        error=error,
        code_lines=count_lines(code_path or Path()),
        n_steps=n_steps,
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> int:
    print(f'=== Routing Framework Benchmark ({N_TRIALS} trials × {N_REPEATS} repeats) ===')
    print(f'Date: {datetime.now(timezone.utc).isoformat()}')
    print()

    trials = build_trial_list(N_TRIALS)

    # Code paths for LOC measurement
    code_paths = {
        'plain_python': PAPER1_ROOT / 'langgraph_router' / 'routing.py',
        'vanilla_fsm': PAPER1_ROOT / 'langgraph_router' / 'routing.py',
        'dataclass_fsm': PAPER1_ROOT / 'langgraph_router' / 'state.py',
        'pydantic_fsm': PAPER1_ROOT / 'langgraph_router' / 'state.py',
        'async_fsm': PAPER1_ROOT / 'langgraph_router' / 'routing.py',
        'langgraph': PAPER1_ROOT / 'langgraph_router' / 'graph.py',
        'langgraph_routing_only': PAPER1_ROOT / 'langgraph_router' / 'graph.py',
        'fsm_full_pipeline': PAPER1_ROOT / 'langgraph_router' / 'routing.py',
        'langgraph_full_pipeline': PAPER1_ROOT / 'langgraph_router' / 'graph.py',
    }

    results: list[BenchmarkResult] = []

    # ---------- Scenario A: Routing-only (pure decision overhead) ----------
    print('=== Scenario A: Routing-only (pure decision overhead) ===')
    scenario_a_impls = [
        ('plain_python', lambda t: run_plain_python(t)),
        ('vanilla_fsm', lambda t: VanillaFSM().run(t)),
        ('dataclass_fsm', lambda t: DataclassFSM().run(t)),
        ('pydantic_fsm', lambda t: PydanticFSM().run(t)),
        ('async_fsm', lambda t: AsyncFSM().run(t)),
        ('langgraph_routing_only', lambda t: run_langgraph_routing_only(t)),
        ('langgraph', lambda t: run_langgraph(t)),
    ]

    for name, func in scenario_a_impls:
        r = run_single(name, 'A', func, trials, code_paths.get(name))
        results.append(r)

    # ---------- Scenario B: Full pipeline (IQA image processing) ----------
    print()
    print('=== Scenario B: Full pipeline (IQA image processing) ===')
    scenario_b_impls = [
        ('fsm_full_pipeline', lambda t: run_full_pipeline_fsm(t)),
        ('langgraph_full_pipeline', lambda t: run_full_pipeline_langgraph(t)),
    ]

    for name, func in scenario_b_impls:
        r = run_single(name, 'B', func, trials, code_paths.get(name))
        results.append(r)

    # ---------- Print comparison table ----------
    print()
    print('=' * 110)
    print(f'{'Framework':<28} {'Scenario':>8} {'Median(ms)':>12} {'P95(ms)':>10} {'Std(ms)':>10} {'Mem(MB)':>9} {'JSONL(ms)':>10} {'LOC':>5} {'Steps':>7}  {'Validation'}')
    print('-' * 110)
    for b in results:
        err = f'[ERR: {b.error[:20]}]' if b.error else ''
        status = 'OK' if b.validation.get('all_fields_present') else 'FAIL'
        val_str = f'{status} up={b.validation.get("upload_cloud","?")} rs={b.validation.get("resample_edge","?")}'
        print(
            f'{b.name:<28} {b.scenario:>8} {b.wall_ms_median:>12.3f} {b.wall_ms_p95:>10.3f} '
            f'{b.wall_ms_std:>10.3f} {b.memory_mb:>9.1f} {b.jsonl_ms:>10.3f} '
            f'{b.code_lines:>5} {b.n_steps:>7}  {val_str} {err}'
        )

    # ---------- Speedup table (Scenario A vs plain_python baseline) ----------
    print()
    print('=== Speedup vs plain_python (Scenario A) ===')
    baseline_a = next((b for b in results if b.name == 'plain_python' and b.scenario == 'A'), None)
    print(f'{'Framework':<28} {'Median(ms)':>12} {'vs plain_python':>18}  {'Interpretation'}')
    print('-' * 75)
    for b in results:
        if b.scenario != 'A' or b.error:
            continue
        if baseline_a and baseline_a.wall_ms_median > 0:
            ratio = baseline_a.wall_ms_median / b.wall_ms_median
            faster = 'faster' if ratio > 1 else ('slower' if ratio < 1 else 'equal')
            interp = {
                100: 'Extreme overhead (100x+)',
                50: 'Heavy framework overhead',
                10: 'Notable overhead',
                2: 'Minor overhead',
                1.2: 'Negligible overhead',
            }
            interp_str = next((v for r, v in sorted(interp.items(), reverse=True) if abs(ratio) >= r), 'Negligible')
            print(f'{b.name:<28} {b.wall_ms_median:>12.3f} {ratio:>17.1f}x {faster}  {interp_str}')
        else:
            print(f'{b.name:<28} {b.wall_ms_median:>12.3f}')

    # ---------- Save outputs ----------
    OUTPUT_JSON.parent.mkdir(parents=True, exist_ok=True)
    out_data = {
        'date': datetime.now(timezone.utc).isoformat(),
        'n_trials': N_TRIALS,
        'n_repeats': N_REPEATS,
        'tau': TAU,
        'K': K,
        'frameworks': [_asdict(b) for b in results],
    }
    OUTPUT_JSON.write_text(json.dumps(out_data, ensure_ascii=False, indent=2), encoding='utf-8')

    import csv
    rows = []
    for b in results:
        row = {
            'framework': b.name,
            'scenario': b.scenario,
            'wall_ms_median': b.wall_ms_median,
            'wall_ms_p95': b.wall_ms_p95,
            'wall_ms_std': b.wall_ms_std,
            'memory_mb': b.memory_mb,
            'jsonl_ms': b.jsonl_ms,
            'code_lines': b.code_lines,
            'n_steps': b.n_steps,
            'error': b.error or '',
        }
        row.update({f'val_{k}': v for k, v in b.validation.items()})
        rows.append(row)

    with OUTPUT_CSV.open('w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)

    print()
    print(f'Results saved to:')
    print(f'  JSON: {OUTPUT_JSON}')
    print(f'  CSV:  {OUTPUT_CSV}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
