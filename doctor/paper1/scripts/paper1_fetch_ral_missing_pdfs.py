#!/usr/bin/env python3
"""Resolve OA PDF URLs for RA-L missing cites via OpenAlex + Unpaywall, then download."""

from __future__ import annotations

import json
import re
import sys
import time
from pathlib import Path

import httpx

PAPER1 = Path(__file__).resolve().parents[1]
CURATED = PAPER1 / 'data/papers/ral_missing_curated.json'
OUT_JSON = PAPER1 / 'data/papers/ral_missing_resolved.json'
PAPERS_DIR = PAPER1 / 'data/papers'
UNPAYWALL_EMAIL = 'paper1-scholar@tyut.edu.cn'
OPENALEX = 'https://api.openalex.org/works/https://doi.org/'


def openalex_enrich(doi: str) -> dict:
    url = OPENALEX + doi
    try:
        r = httpx.get(url, timeout=30, headers={'User-Agent': 'paper1-scholar/1.0'})
        if r.status_code != 200:
            return {}
        w = r.json()
        oa = w.get('open_access') or {}
        loc = w.get('primary_location') or {}
        pdf = oa.get('oa_url') or loc.get('pdf_url') or ''
        arxiv = ''
        for loc_item in w.get('locations') or []:
            src = (loc_item.get('source') or {}).get('display_name', '')
            lid = loc_item.get('id') or ''
            if 'arxiv' in lid.lower() or 'arxiv' in src.lower():
                m = re.search(r'(\d{4}\.\d{4,5})', lid)
                if m:
                    arxiv = m.group(1)
                    if not pdf:
                        pdf = f'https://arxiv.org/pdf/{arxiv}'
        ids = w.get('ids') or {}
        if not arxiv and ids.get('arxiv'):
            arxiv = ids['arxiv'].split('/')[-1]
            if not pdf:
                pdf = f'https://arxiv.org/pdf/{arxiv}'
        return {
            'openalex_title': w.get('title', ''),
            'is_oa': oa.get('is_oa', False),
            'pdf_url': pdf,
            'arxiv_id': arxiv,
            'landing_url': oa.get('oa_url') or loc.get('landing_page_url') or '',
        }
    except Exception as exc:
        return {'error': str(exc)}


def unpaywall_pdf(doi: str) -> str:
    try:
        r = httpx.get(
            f'https://api.unpaywall.org/v2/{doi}',
            params={'email': UNPAYWALL_EMAIL},
            timeout=20,
        )
        if r.status_code != 200:
            return ''
        d = r.json()
        best = d.get('best_oa_location') or {}
        return best.get('url_for_pdf') or best.get('url') or ''
    except Exception:
        return ''


def main() -> int:
    curated = json.loads(CURATED.read_text())
    resolved = []
    for p in curated:
        doi = p.get('doi', '')
        entry = {**p}
        if p.get('pdf_url'):
            entry['resolve_source'] = 'curated_arxiv'
        else:
            oa = openalex_enrich(doi) if doi else {}
            entry.update(oa)
            if not entry.get('pdf_url') and doi:
                up = unpaywall_pdf(doi)
                if up:
                    entry['pdf_url'] = up
                    entry['resolve_source'] = 'unpaywall'
            elif entry.get('pdf_url'):
                entry['resolve_source'] = entry.get('resolve_source') or 'openalex'
        resolved.append(entry)
        time.sleep(0.3)

    OUT_JSON.write_text(json.dumps(resolved, ensure_ascii=False, indent=2) + '\n')
    print(f'Wrote {OUT_JSON}')
    for e in resolved:
        key = e.get('cite_key', '?')
        pdf = e.get('pdf_url', '')
        print(f'  {key}: {"PDF " + pdf[:60] if pdf else "NO OA PDF"}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
