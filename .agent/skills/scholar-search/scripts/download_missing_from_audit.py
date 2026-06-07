#!/usr/bin/env python3
"""Download and map missing PDFs from Paper I cite_audit.json.

The script intentionally uses legal/auditable sources only:
- existing local PDFs under data/papers/
- curated official/arXiv PDF URLs
- direct pdf_url entries in curated JSON
- Unpaywall open-access locations

It updates cite_key_map.json and writes a timestamped report.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import httpx

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - optional convenience dependency
    def load_dotenv(*_args: Any, **_kwargs: Any) -> None:
        return None

ROOT = Path(__file__).resolve().parents[4]
ENV_FILE = ROOT / '.env.scholar'
if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

DEFAULT_PAPER_ROOT = ROOT / 'doctor/paper1'
DEFAULT_PAPERS_DIR = DEFAULT_PAPER_ROOT / 'data/papers'
DEFAULT_AUDIT = DEFAULT_PAPERS_DIR / 'cite_audit.json'
DEFAULT_MAP = DEFAULT_PAPERS_DIR / 'cite_key_map.json'
DEFAULT_REPORT_DIR = DEFAULT_PAPER_ROOT / 'docs'
UNPAYWALL_EMAIL = os.environ.get('UNPAYWALL_EMAIL', 'paper1@example.invalid')

# Curated legal/open URLs for cited papers where DOI OA lookup is often weak.
# Keep these to author, publisher OA, arXiv, or other auditable open locations.
CURATED_PDF_URLS: dict[str, list[str]] = {
    'chen2021telemed': [
        'https://link.springer.com/content/pdf/10.1186/s12889-020-09301-4.pdf'
    ],
    'howard2019mobilenetv3': ['https://arxiv.org/pdf/1905.02244'],
    'wang2014edge': ['https://arxiv.org/pdf/1603.07906'],
    'schick2023toolformer': ['https://arxiv.org/pdf/2302.04761'],
    'ke2021musiq': ['https://arxiv.org/pdf/2108.05997'],
    'chen2024topiq': ['https://arxiv.org/pdf/2308.03060'],
    'mittal2012brisque': [
        'https://live.ece.utexas.edu/research/quality/brisque_journal.pdf'
    ],
    'mittal2012niqe': [
        'https://live.ece.utexas.edu/research/quality/niqe_spl.pdf'
    ],
}


def norm(text: str) -> str:
    return re.sub(r'[^a-z0-9]+', ' ', text.lower()).strip()


def tokens(text: str) -> set[str]:
    stop = {
        'a', 'an', 'and', 'are', 'as', 'by', 'for', 'from', 'in', 'of', 'on', 'or',
        'the', 'to', 'with', 'using', 'via', 'during', 'is', 'can', 'it',
    }
    return {t for t in norm(text).split() if len(t) > 2 and t not in stop}


def safe_title(title: str, max_len: int = 58) -> str:
    cleaned = re.sub(r'[^\w\s-]', '', title)
    cleaned = re.sub(r'\s+', '_', cleaned.strip())
    return cleaned[:max_len] or 'untitled'


def filename_for(row: dict[str, Any]) -> str:
    year = row.get('year') or ''
    if not year:
        m = re.search(r'(19|20)\d{2}', row.get('doi', '') + ' ' + row.get('title', ''))
        year = m.group(0) if m else 'nodate'
    key = row['cite_key']
    return f'{year}_{key}_{safe_title(row.get("title", ""))}.pdf'


def load_json(path: Path, default: Any) -> Any:
    if path.exists():
        return json.loads(path.read_text(encoding='utf-8'))
    return default


def save_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


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


def get_bib_metadata(paper_root: Path) -> dict[str, dict[str, str]]:
    bib = paper_root / 'latex/references.bib'
    text = bib.read_text(encoding='utf-8') if bib.exists() else ''
    meta: dict[str, dict[str, str]] = {}
    for key, block in _entry_blocks(text).items():
        meta[key] = {
            'title': _field(block, 'title'),
            'year': _field(block, 'year'),
            'doi': _field(block, 'doi'),
            'url': _field(block, 'url'),
        }
    return meta


def pdf_text(path: Path, max_chars: int = 20000) -> str:
    if shutil.which('pdftotext') is None:
        return ''
    try:
        out = subprocess.run(
            ['pdftotext', str(path), '-'],
            check=False,
            capture_output=True,
            text=True,
            timeout=20,
        )
        return out.stdout[:max_chars]
    except Exception:
        return ''


def verify_pdf(path: Path, title: str) -> tuple[bool, str]:
    if not path.exists() or path.stat().st_size < 1000:
        return False, 'missing_or_too_small'
    head = path.read_bytes()[:5]
    if not head.startswith(b'%PDF'):
        return False, 'not_pdf_magic'
    title_tokens = tokens(title)
    if not title_tokens:
        return True, 'pdf_magic_only'
    text = norm(pdf_text(path))
    if not text:
        return True, 'pdf_magic_only_no_text'
    hits = sum(1 for t in title_tokens if t in text)
    ratio = hits / max(len(title_tokens), 1)
    if ratio >= 0.45:
        return True, f'title_token_match_{hits}/{len(title_tokens)}'
    return False, f'weak_title_match_{hits}/{len(title_tokens)}'


def candidate_existing(row: dict[str, Any], papers_dir: Path) -> tuple[Path | None, str]:
    title_toks = tokens(row.get('title', ''))
    key = row.get('cite_key', '').lower()
    best: tuple[float, Path | None, str] = (0.0, None, '')
    for pdf in papers_dir.glob('*.pdf'):
        hay = norm(pdf.stem)
        key_bonus = 0.35 if key and key in hay else 0.0
        overlap = len(title_toks & set(hay.split())) / max(len(title_toks), 1)
        score = overlap + key_bonus
        if score > best[0]:
            best = (score, pdf, f'filename_score_{score:.2f}')
    if best[1] and best[0] >= 0.42:
        ok, note = verify_pdf(best[1], row.get('title', ''))
        if ok:
            return best[1], f'existing:{best[2]}:{note}'
    return None, ''


def download_url(url: str, dest: Path, trust_env: bool) -> tuple[bool, str]:
    if not url:
        return False, 'empty_url'
    try:
        with httpx.stream('GET', url, follow_redirects=True, timeout=90, trust_env=trust_env) as resp:
            if resp.status_code != 200:
                return False, f'http_{resp.status_code}'
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open('wb') as f:
                first = True
                for chunk in resp.iter_bytes(chunk_size=65536):
                    if first and not chunk.startswith(b'%PDF'):
                        return False, 'not_pdf_response'
                    first = False
                    f.write(chunk)
        if dest.exists() and dest.stat().st_size > 1000:
            return True, 'downloaded'
        return False, 'too_small'
    except Exception as exc:
        return False, f'error:{exc}'


def windows_powershell_download_url(url: str, dest: Path) -> tuple[bool, str]:
    ps = Path('/mnt/c/Windows/System32/WindowsPowerShell/v1.0/powershell.exe')
    if not ps.exists():
        return False, 'powershell_not_found'
    try:
        win_dest = subprocess.run(
            ['wslpath', '-w', str(dest)],
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        dest.parent.mkdir(parents=True, exist_ok=True)

        def ps_quote(value: str) -> str:
            return "'" + value.replace("'", "''") + "'"

        command = (
            '$ProgressPreference = "SilentlyContinue"; '
            f'Invoke-WebRequest -UseBasicParsing -Uri {ps_quote(url)} '
            f'-OutFile {ps_quote(win_dest)}'
        )
        out = subprocess.run(
            [str(ps), '-NoProfile', '-Command', command],
            check=False,
            capture_output=True,
            text=True,
            timeout=180,
        )
        if out.returncode != 0:
            detail = (out.stderr or out.stdout).strip().replace('\n', ' ')[:240]
            return False, f'powershell_error:{detail}'
        if dest.exists() and dest.stat().st_size > 1000:
            return True, 'downloaded:powershell'
        return False, 'powershell_too_small'
    except Exception as exc:
        return False, f'powershell_exception:{exc}'


def unpaywall_url(doi: str) -> str:
    if not doi:
        return ''
    if UNPAYWALL_EMAIL.endswith('.invalid'):
        return ''
    try:
        url = f'https://api.unpaywall.org/v2/{doi}?email={UNPAYWALL_EMAIL}'
        resp = httpx.get(url, timeout=30, follow_redirects=True, trust_env=True)
        if resp.status_code != 200:
            return ''
        data = resp.json()
        loc = data.get('best_oa_location') or {}
        return loc.get('url_for_pdf') or loc.get('url') or ''
    except Exception:
        return ''


def rows_from_audit(audit: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for row in audit.get('ral_citations', []):
        if row.get('pdf_status') == 'on_disk':
            continue
        rows.append(dict(row))
    return rows


def main() -> None:
    ap = argparse.ArgumentParser(description='Download/map missing Paper I citation PDFs.')
    ap.add_argument('--paper-root', default=str(DEFAULT_PAPER_ROOT))
    ap.add_argument('--audit', default=str(DEFAULT_AUDIT))
    ap.add_argument('--papers-dir', default=str(DEFAULT_PAPERS_DIR))
    ap.add_argument('--map-file', default=str(DEFAULT_MAP))
    ap.add_argument('--report-dir', default=str(DEFAULT_REPORT_DIR))
    ap.add_argument('--no-download', action='store_true', help='Only map existing files.')
    ap.add_argument(
        '--network-mode',
        choices=('auto', 'env', 'direct'),
        default='auto',
        help='env uses HTTP(S)_PROXY, direct ignores proxy env, auto tries env then direct.',
    )
    ap.add_argument(
        '--windows-fallback',
        action='store_true',
        help='If WSL networking fails, download via Windows PowerShell and write back to WSL path.',
    )
    ap.add_argument('--only', nargs='*', default=[], help='Optional cite keys to process.')
    args = ap.parse_args()

    paper_root = Path(args.paper_root)
    audit_path = Path(args.audit)
    papers_dir = Path(args.papers_dir)
    map_file = Path(args.map_file)
    report_dir = Path(args.report_dir)
    audit = load_json(audit_path, {})
    cite_map = load_json(
        map_file,
        {
            'updated': '',
            'description': 'Maps BibTeX cite keys to local PDF filenames under data/papers/',
            'ral_manuscript_citations': {},
            'notes': {},
        },
    )
    cite_map.setdefault('ral_manuscript_citations', {})
    cite_map.setdefault('notes', {})
    bib_meta = get_bib_metadata(paper_root)

    rows = rows_from_audit(audit)
    if args.only:
        want = set(args.only)
        rows = [r for r in rows if r['cite_key'] in want]

    results = []
    for row in rows:
        key = row['cite_key']
        if key in bib_meta:
            for field in ('title', 'doi', 'url'):
                if bib_meta[key].get(field):
                    row[field] = bib_meta[key][field]
            row['year'] = bib_meta[key].get('year', '')
        result = {'cite_key': key, 'title': row.get('title', ''), 'status': 'failed', 'detail': ''}

        existing, note = candidate_existing(row, papers_dir)
        if existing:
            cite_map['ral_manuscript_citations'][key] = existing.name
            result.update(status='mapped_existing', detail=note, filename=existing.name)
            results.append(result)
            continue

        if args.no_download:
            result['detail'] = 'no_existing_match'
            results.append(result)
            continue

        urls: list[str] = []
        if key in CURATED_PDF_URLS:
            curated = CURATED_PDF_URLS[key]
            urls.extend(curated if isinstance(curated, list) else [curated])
        doi = row.get('doi', '')
        oa = unpaywall_url(doi)
        if oa:
            urls.append(oa)

        for url in urls:
            dest = papers_dir / filename_for(row)
            attempts = [True, False] if args.network_mode == 'auto' else [args.network_mode == 'env']
            ok = False
            detail = ''
            for trust_env in attempts:
                ok, detail = download_url(url, dest, trust_env=trust_env)
                if ok:
                    detail = f'{detail}:trust_env={trust_env}'
                    break
                if dest.exists() and dest.stat().st_size < 1000:
                    dest.unlink()
            if not ok:
                if args.windows_fallback:
                    ok, detail = windows_powershell_download_url(url, dest)
                if not ok:
                    result['detail'] = f'{url}:{detail}'
                    continue
            verified, vnote = verify_pdf(dest, row.get('title', ''))
            if not verified:
                result['detail'] = f'{url}:{vnote}'
                dest.unlink(missing_ok=True)
                continue
            cite_map['ral_manuscript_citations'][key] = dest.name
            result.update(status='downloaded', detail=f'{url}:{vnote}', filename=dest.name)
            break

        results.append(result)
        time.sleep(0.5)

    cite_map['updated'] = time.strftime('%Y-%m-%d')
    save_json(map_file, cite_map)

    report_dir.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime('%Y%m%d-%H%M%S')
    report = report_dir / f'{stamp}-scholar-search-missing-download-report.md'
    lines = [
        '# scholar-search 未归档文献下载/映射报告',
        '',
        f'> 时间戳: {stamp}',
        f'> audit: `{audit_path}`',
        f'> map: `{map_file}`',
        '',
        '| cite key | status | local file | detail |',
        '|----------|--------|------------|--------|',
    ]
    for r in results:
        lines.append(
            f"| `{r['cite_key']}` | {r['status']} | `{r.get('filename', '')}` | {r.get('detail', '')} |"
        )
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Wrote {report}')
    print(json.dumps({'processed': len(results), 'report': str(report)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
