#!/usr/bin/env python3
"""Audit RA-L \\cite keys vs local PDFs under doctor/paper1/data/papers/."""

from __future__ import annotations

import json
import re
from pathlib import Path

PAPER1_ROOT = Path(__file__).resolve().parents[1]
BIB = PAPER1_ROOT / 'latex/references.bib'
RAL_DIR = PAPER1_ROOT / 'latex/sections/ral'
PAPERS_DIR = PAPER1_ROOT / 'data/papers'
OUT = PAPERS_DIR / 'cite_audit.json'

# bib key -> local PDF filename (verified on disk)
BIB_TO_PDF = {
    'su2020hyperiqa': '2020_Su_HyperIQA_Blindly_Assess_Image_Quality_in_the_Wild_.pdf',
    'wang2023clipiqa': '2023_Wang_Exploring_CLIP_for_Assessing_the_Look_and_Feel_of_.pdf',
    'zhou2019edge': '2019_Zhou_Edge_Intelligence_Paving_the_Last_Mile_of_Artifici.pdf',
    'sandler2018mobilenetv2': (
        '2018_Sandler_MobileNetV2_Inverted_Residuals_and_Linear_Bottlene.pdf'
    ),
    'yao2023react': '2023_Yao_ReAct_Synergizing_Reasoning_and_Acting_in_Language.pdf',
    'moore2021ros2': (
        '2022_Macenski_Robot_Operating_System_2_Design_Architecture_and_U.pdf'
    ),
}

# Optional: merge cite_key_map.json if present
_MAP_FILE = PAPERS_DIR / 'cite_key_map.json'


def _load_cite_map() -> dict[str, str | None]:
    mapping: dict[str, str | None] = dict(BIB_TO_PDF)
    if _MAP_FILE.exists():
        data = json.loads(_MAP_FILE.read_text())
        for k, v in (data.get('ral_manuscript_citations') or {}).items():
            if v:
                mapping[k] = v
    return mapping


def _entry_blocks(text: str) -> dict[str, str]:
    blocks: dict[str, str] = {}
    for m in re.finditer(r'@\w+\{([^,]+),', text):
        key = m.group(1)
        start = m.start()
        depth = 0
        end = len(text)
        for i, ch in enumerate(text[start:], start=start):
            if ch == '{':
                depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        blocks[key] = text[start:end]
    return blocks


def _field(block: str, field: str) -> str:
    m = re.search(rf'{field}\s*=\s*\{{', block, re.I)
    if not m:
        return ''
    start = m.end()
    depth = 1
    chars: list[str] = []
    for ch in block[start:]:
        if ch == '{':
            depth += 1
            chars.append(ch)
        elif ch == '}':
            depth -= 1
            if depth == 0:
                break
            chars.append(ch)
        else:
            chars.append(ch)
    return ''.join(chars).strip()


def parse_bib(text: str) -> dict[str, dict[str, str]]:
    entries: dict[str, dict[str, str]] = {}
    for key, block in _entry_blocks(text).items():
        entries[key] = {
            'title': _field(block, 'title'),
            'year': _field(block, 'year'),
            'doi': _field(block, 'doi'),
            'url': _field(block, 'url'),
        }
    return entries


def ral_cite_keys() -> set[str]:
    keys: set[str] = set()
    for tex in RAL_DIR.glob('*.tex'):
        for m in re.finditer(r'\\cite[a-z]*\{([^}]+)\}', tex.read_text()):
            for k in m.group(1).split(','):
                keys.add(k.strip())
    return keys


def main() -> None:
    bib_e = parse_bib(BIB.read_text())
    cite_keys = ral_cite_keys()
    bib_to_pdf = _load_cite_map()
    pdfs = {p.name: p.stat().st_size for p in PAPERS_DIR.glob('*.pdf')}
    index_path = PAPERS_DIR / 'papers_index.json'
    index = json.loads(index_path.read_text())['papers'] if index_path.exists() else {}

    ral_rows = []
    for k in sorted(cite_keys):
        meta = bib_e.get(k, {})
        pdf = bib_to_pdf.get(k)
        if pdf and pdf not in pdfs:
            pdf = None
        ral_rows.append(
            {
                'cite_key': k,
                'title': meta.get('title', ''),
                'doi': meta.get('doi', ''),
                'local_pdf': pdf,
                'pdf_status': 'on_disk' if pdf else 'not_in_papers_dir',
            }
        )

    pdf_rows = []
    for fn, sz in sorted(pdfs.items()):
        meta = next((v for v in index.values() if v.get('filename') == fn), {})
        cited = any(bib_to_pdf.get(ck) == fn for ck in cite_keys)
        note = ''
        if 'GPT-4' in meta.get('title', ''):
            note = 'WRONG_PAPER: not OpenAI GPT-4 arXiv:2303.08774'
        pdf_rows.append(
            {
                'filename': fn,
                'size_bytes': sz,
                'title': meta.get('title', ''),
                'doi_index': meta.get('doi', ''),
                'cited_in_ral': cited,
                'authenticity_note': note,
            }
        )

    audit = {
        'generated': __import__('datetime').date.today().isoformat(),
        'manuscript': 'latex/main-ral.tex + sections/ral/*.tex',
        'references_bib': str(BIB.relative_to(PAPER1_ROOT)),
        'ral_cite_count': len(cite_keys),
        'ral_cites_with_local_pdf': sum(1 for r in ral_rows if r['pdf_status'] == 'on_disk'),
        'ral_cites_without_local_pdf': sum(
            1 for r in ral_rows if r['pdf_status'] != 'on_disk'
        ),
        'local_pdf_count': len(pdfs),
        'ral_citations': ral_rows,
        'local_pdfs': pdf_rows,
    }
    OUT.write_text(json.dumps(audit, indent=2, ensure_ascii=False) + '\n')
    print(
        f'Wrote {OUT}: RA-L cites {audit["ral_cite_count"]}, '
        f'with PDF {audit["ral_cites_with_local_pdf"]}, '
        f'without PDF {audit["ral_cites_without_local_pdf"]}'
    )


if __name__ == '__main__':
    main()
