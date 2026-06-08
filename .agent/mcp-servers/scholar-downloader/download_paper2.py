import os
from pathlib import Path
from download_lib import load_paper_config, download_batch, write_manifest, format_results_summary, dest_path_for, is_valid_pdf

OUTPUT_DIR = Path("/home/ros/work/paper2/doctor/paper2/data/papers")
CONFIG = Path("/home/ros/work/paper2/.agent/mcp-servers/scholar-downloader/config/paper2_missing.json")
USE_SCIHUB = True

def main():
    papers = load_paper_config(CONFIG)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    need = [p for p in papers if not is_valid_pdf(dest_path_for(OUTPUT_DIR, p))]
    if not need:
        print("All PDFs already exist.")
        return 0
    
    print(f"Downloading {len(need)} papers...")
    results = download_batch(need, OUTPUT_DIR, use_scihub=USE_SCIHUB, delay_sec=1.5)
    
    # We won't use Playwright for fallback automatically in this simple script,
    # as we want to test if the basic strategies work, and replace DOIs if they fail.
    
    from download_lib import DownloadResult
    batch_map = {r.citeKey: r for r in results}
    merged = []
    for p in papers:
        if p.citeKey in batch_map:
            merged.append(batch_map[p.citeKey])
        elif is_valid_pdf(dest_path_for(OUTPUT_DIR, p)):
            merged.append(DownloadResult(p.citeKey, p.doi, True, str(dest_path_for(OUTPUT_DIR, p)), "existing"))
        else:
            merged.append(DownloadResult(p.citeKey, p.doi, False, None, None, "missing"))
            
    manifest = write_manifest(merged, OUTPUT_DIR)
    print(format_results_summary(merged))
    return 0 if all(r.ok for r in merged) else 1

if __name__ == "__main__":
    raise SystemExit(main())
