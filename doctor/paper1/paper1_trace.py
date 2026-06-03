"""Structured trace logging for Paper I experiments (timestamp, file, line, func, args)."""

from __future__ import annotations

import functools
import inspect
import logging
import os
import sys
from pathlib import Path
from typing import Any, Callable, TypeVar

F = TypeVar('F', bound=Callable[..., Any])

_CONFIGURED = False
_LOG_FORMAT = (
    '%(asctime)s | %(levelname)s | %(name)s | '
    '%(filename)s:%(lineno)d | %(funcName)s | %(message)s'
)
_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def _safe_repr(obj: Any, max_len: int = 240) -> str:
    try:
        text = repr(obj)
    except Exception as exc:  # noqa: BLE001
        text = f'<unreprable {type(obj).__name__}: {exc}>'
    if len(text) > max_len:
        return text[: max_len - 3] + '...'
    return text


def init_trace(
    module_file: str | None = None,
    *,
    level: int = logging.INFO,
    log_file: Path | str | None = None,
) -> logging.Logger:
    """Configure root logger once; attach file handler if PAPER1_LOG_FILE set."""
    global _CONFIGURED
    name = 'paper1'
    if module_file:
        name = Path(module_file).stem
    logger = logging.getLogger('paper1')
    if _CONFIGURED:
        return logger.getChild(name)

    logger.setLevel(level)
    logger.propagate = False
    formatter = logging.Formatter(_LOG_FORMAT, datefmt=_DATE_FORMAT)

    stream = logging.StreamHandler(sys.stdout)
    stream.setFormatter(formatter)
    logger.addHandler(stream)

    log_path = log_file or os.environ.get('PAPER1_LOG_FILE')
    if log_path:
        path = Path(log_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(path, encoding='utf-8', mode='a')
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    logger.info(
        'init_trace module=%s trace_frames=%s log_file=%s',
        module_file or '-',
        os.environ.get('PAPER1_TRACE_FRAMES', '0'),
        log_path or '-',
    )
    _CONFIGURED = True
    return logger.getChild(name)


def trace_call(
    *,
    log_result: bool = True,
    log_frames: bool | None = None,
) -> Callable[[F], F]:
    """Decorator: log ENTER/EXIT with args, kwargs, return value and caller line."""

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            if log_frames is None:
                enabled = os.environ.get('PAPER1_TRACE_FRAMES', '0') == '1'
            else:
                enabled = log_frames
            if not enabled and func.__name__ in ('simulate_frame',):
                return func(*args, **kwargs)

            mod = func.__module__
            qual = f'{mod}.{func.__qualname__}'
            log = logging.getLogger('paper1').getChild(Path(mod).stem if mod else 'anon')
            frame = inspect.currentframe()
            caller = frame.f_back if frame else None
            caller_loc = ''
            if caller is not None:
                caller_loc = f'{caller.f_code.co_filename}:{caller.f_lineno}'

            arg_sig = ', '.join(_safe_repr(a) for a in args)
            kw_sig = ', '.join(f'{k}={_safe_repr(v)}' for k, v in kwargs.items())
            log.info(
                'ENTER %s | called_from=%s | args=(%s) | kwargs={%s}',
                qual,
                caller_loc,
                arg_sig,
                kw_sig,
            )
            try:
                out = func(*args, **kwargs)
            except Exception:
                log.exception('RAISE %s | called_from=%s', qual, caller_loc)
                raise
            if log_result:
                log.info('EXIT %s | return=%s', qual, _safe_repr(out))
            else:
                log.info('EXIT %s', qual)
            return out

        return wrapper  # type: ignore[misc]

    return decorator


def log_progress(
    logger: logging.Logger,
    current: int,
    total: int,
    *,
    every: int = 50,
    label: str = '',
    extra: str = '',
) -> None:
    """Emit periodic progress lines (1-based current)."""
    if total <= 0:
        return
    if current == 1 or current == total or current % every == 0:
        pct = 100.0 * current / total
        msg = f'PROGRESS {label} {current}/{total} ({pct:.1f}%)'
        if extra:
            msg = f'{msg} | {extra}'
        logger.info(msg)
