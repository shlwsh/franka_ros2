"""Shared LaTeX table wrappers for two-column Paper I drafts."""

from __future__ import annotations

from typing import Iterable


def wrap_tabular(
    col_spec: str,
    body_lines: Iterable[str],
    *,
    width: str = r'\columnwidth',
) -> list[str]:
    """Return resizebox-wrapped tabular lines (no caption/label)."""
    lines = [r'\small', rf'\resizebox{{{width}}}{{!}}{{%', rf'\begin{{tabular}}{{{col_spec}}}']
    lines.extend(body_lines)
    # body_lines should include \hline rows; do not add extra rules here
    lines.extend([r'\end{tabular}%', '}'])
    return lines
