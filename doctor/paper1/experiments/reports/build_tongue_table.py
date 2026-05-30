#!/usr/bin/env python3
"""Build ShezhenV3 tongue condition table for LaTeX."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[2]
CFG = PAPER1_ROOT / 'experiments/configs/tcm_paths.yaml'

# English gloss for paper (research names kept romanized)
GLOSS = {
    'jiankangshe': 'Healthy tongue',
    'botaishe': 'Peeling tongue',
    'hongshe': 'Red tongue',
    'zishe': 'Purple tongue',
    'pangdashe': 'Chubby tongue',
    'shoushe': 'Thin tongue',
    'hongdianshe': 'Red-spot tongue',
    'liewenshe': 'Fissured tongue',
    'chihenshe': 'Tooth-marked tongue',
    'baitaishe': 'White-coating tongue',
}


def main() -> None:
    import yaml

    root = Path(yaml.safe_load(CFG.read_text())['dataset_root'])
    counts = Counter()
    id2name = {}
    for split in ['train', 'val', 'test']:
        d = json.loads((root / split / 'annotations' / f'{split}.json').read_text())
        id2name.update({c['id']: c['name'] for c in d['categories']})
        for a in d['annotations']:
            cid = a['category_id']
            if cid in id2name:
                counts[id2name[cid]] += 1

    def write(out: Path, en: bool):
        lines = [
            '% Auto-generated tongue condition counts',
            '\\begin{table}[t]',
            '\\centering',
            (
                '\\caption{ShezhenV3-COCO annotation counts by tongue condition (all splits).}'
                if en
                else '\\caption{ShezhenV3-COCO 各舌象类别标注数（全划分合计）。}'
            ),
            '\\label{' + ('tab:tongue-conditions' if en else 'tab:tongue-conditions-zh') + '}',
            '\\small',
            '\\begin{tabular}{llr}',
            '\\hline',
            ('Code name & Gloss & \\#Annotations \\\\' if en else '代号 & 含义 & 标注数 \\\\'),
            '\\hline',
        ]
        for name, n in counts.most_common():
            gloss = GLOSS.get(name, name)
            lines.append(f'\\texttt{{{name}}} & {gloss} & {n} \\\\')
        lines.extend(['\\hline', '\\end{tabular}', '\\end{table}', ''])
        out.write_text('\n'.join(lines), encoding='utf-8')

    write(PAPER1_ROOT / 'latex/sections/table_tongue_conditions.tex', True)
    write(PAPER1_ROOT / 'latex/sections/zh/table_tongue_conditions.tex', False)
    print('Wrote tongue condition tables', sum(counts.values()), 'annotations')


if __name__ == '__main__':
    main()
