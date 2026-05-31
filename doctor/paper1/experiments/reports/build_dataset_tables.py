#!/usr/bin/env python3
"""Generate dataset statistics LaTeX tables (EN + ZH)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from latex_table_wrap import wrap_tabular

PAPER1_ROOT = Path(__file__).resolve().parents[2]


def emit_split_table(
    *,
    comment: str,
    caption: str,
    label: str,
    header: str,
    rows: list[str],
    col_spec: str = 'lrr',
) -> list[str]:
    body = [r'\hline', header, r'\hline', *rows, r'\hline']
    return [
        comment,
        r'\begin{table}[t]',
        r'\centering',
        f'\\caption{{{caption}}}',
        f'\\label{{{label}}}',
        *wrap_tabular(col_spec, body),
        r'\end{table}',
        '',
    ]


def main() -> None:
    meta = json.loads((PAPER1_ROOT / 'experiments/splits/tcm_meta.json').read_text(encoding='utf-8'))
    cal: dict = {}
    cal_path = PAPER1_ROOT / 'experiments/results/tcm_calibration_stats.json'
    if cal_path.is_file():
        cal = json.loads(cal_path.read_text(encoding='utf-8'))
    cross: dict = {}
    cross_path = PAPER1_ROOT / 'experiments/results/cross_tcm_fd.json'
    if cross_path.is_file():
        cross = json.loads(cross_path.read_text(encoding='utf-8'))

    c = meta['counts']
    en_split_rows = [
        f'Train & {c.get("train", 0)} & held out (future fine-tuning) \\\\',
        f'Validation & {c.get("val", 0)} & Edge-IQA $\\tau$ calibration \\\\',
        f'Test & {c.get("test", 0)} & main matrix (B0--B3) \\\\',
        r'\hline',
        f'Total & {meta.get("total", 0)} & COCO-format bounding boxes \\\\',
    ]
    en_cal_rows = [
        f'Median $Q_{{\\mathrm{{img}}}}$ & {cal.get("median_clear", 0):.3f} & {cal.get("median_blur", 0):.3f} \\\\',
        f'Mean $Q_{{\\mathrm{{img}}}}$ & {cal.get("clear_mean", 0):.3f} & {cal.get("blur_mean", 0):.3f} \\\\',
        f'Std & {cal.get("clear_std", 0):.3f} & {cal.get("blur_std", 0):.3f} \\\\',
        r'\hline',
        f'Routing threshold $\\tau$ & \\multicolumn{{2}}{{c}}{{{cal.get("tau", 0.505):.3f}}} \\\\',
        f'Spearman $\\rho$ (M5) & \\multicolumn{{2}}{{c}}{{{cross.get("spearman", 0):.3f} ($n={cross.get("n", 0)}$)}} \\\\',
    ]
    en = []
    en.extend(
        emit_split_table(
            comment='% Table: ShezhenV3-COCO — auto-generated',
            caption='ShezhenV3-COCO tongue dataset splits used in Paper~I.',
            label='tab:dataset',
            header='Split & Images & Purpose \\\\',
            rows=en_split_rows,
        )
    )
    en.extend(
        emit_split_table(
            comment='',
            caption=(
                'Edge-IQA calibration on ShezhenV3 validation split '
                f'($n={cal.get("n_clear", 0)}$ clear + $n={cal.get("n_blur", 0)}$ synthetic blur).'
            ),
            label='tab:iqa-calibration',
            header='Metric & Clear cohort & Blur cohort \\\\',
            rows=en_cal_rows,
            col_spec='lcc',
        )
    )
    (PAPER1_ROOT / 'latex/sections/table_dataset.tex').write_text('\n'.join(en), encoding='utf-8')

    zh_split_rows = [
        f'训练集 & {c.get("train", 0)} & 预留（未来微调） \\\\',
        f'验证集 & {c.get("val", 0)} & Edge-IQA $\\tau$ 标定 \\\\',
        f'测试集 & {c.get("test", 0)} & 主实验矩阵 B0--B3 \\\\',
        r'\hline',
        f'合计 & {meta.get("total", 0)} & COCO 格式框标注 \\\\',
    ]
    zh_cal_rows = [
        f'$Q_{{\\mathrm{{img}}}}$ 中位数 & {cal.get("median_clear", 0):.3f} & {cal.get("median_blur", 0):.3f} \\\\',
        f'$Q_{{\\mathrm{{img}}}}$ 均值 & {cal.get("clear_mean", 0):.3f} & {cal.get("blur_mean", 0):.3f} \\\\',
        f'标准差 & {cal.get("clear_std", 0):.3f} & {cal.get("blur_std", 0):.3f} \\\\',
        r'\hline',
        f'路由阈值 $\\tau$ & \\multicolumn{{2}}{{c}}{{{cal.get("tau", 0.505):.3f}}} \\\\',
        f'Spearman $\\rho$（M5） & \\multicolumn{{2}}{{c}}{{{cross.get("spearman", 0):.3f}（$n={cross.get("n", 0)}$）}} \\\\',
    ]
    zh = []
    zh.extend(
        emit_split_table(
            comment='% 表：ShezhenV3-COCO — 自动生成',
            caption='Paper~I 使用的 ShezhenV3-COCO 舌象数据集划分。',
            label='tab:dataset-zh',
            header='划分 & 图像数 & 用途 \\\\',
            rows=zh_split_rows,
        )
    )
    zh.extend(
        emit_split_table(
            comment='',
            caption=(
                'ShezhenV3 验证集 Edge-IQA 标定结果'
                f'（清晰 $n={cal.get("n_clear", 0)}$ + 合成模糊 $n={cal.get("n_blur", 0)}$）。'
            ),
            label='tab:iqa-calibration-zh',
            header='指标 & 清晰组 & 模糊组 \\\\',
            rows=zh_cal_rows,
            col_spec='lcc',
        )
    )
    (PAPER1_ROOT / 'latex/sections/zh/table_dataset.tex').write_text('\n'.join(zh), encoding='utf-8')
    print('Wrote table_dataset.tex (EN/ZH)')


if __name__ == '__main__':
    main()
