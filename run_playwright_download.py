import sys
import os
import time

# Disable proxy for local connections
os.environ["no_proxy"] = "*"

def _wsl_windows_host() -> str:
    try:
        with open('/etc/resolv.conf', encoding='utf-8') as f:
            for line in f:
                if line.startswith('nameserver '):
                    return line.split()[1].strip()
    except OSError:
        pass
    return '127.0.0.1'

dois = [
    "10.1109/MRA.2011.2181749",
    "10.1016/j.cmpb.2014.10.001",
    "10.1145/3037697.3037728",
    "10.1109/COMST.2019.2892586",
    "10.1016/j.patcog.2016.01.017",
    "10.1109/JIOT.2016.2579198",
    "10.1109/TCSVT.2018.2866628",
    "10.1007/s10462-019-09735-6"
]

output_dir = "/root/work/paper1/doctor/paper1/data/papers"
os.makedirs(output_dir, exist_ok=True)
debug_host = os.environ.get('CHROME_DEBUG_HOST', _wsl_windows_host())
debug_port = 9222
cdp_url = f"http://{debug_host}:{debug_port}"

print(f"Attempting to connect to Chrome via Playwright at {cdp_url} ...")

from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    try:
        browser = p.chromium.connect_over_cdp(cdp_url)
        print("✅ Successfully connected to Chrome via Playwright!")
        
        # Use the first context (usually the main user profile)
        context = browser.contexts[0]
        page = context.new_page()
        
        for doi in dois:
            print(f"🔄 Processing DOI: {doi}")
            try:
                # Navigate to the DOI
                page.goto(f"https://doi.org/{doi}")
                page.wait_for_timeout(5000) # Wait for page to load and react
                
                safe_name = doi.replace('/', '_').replace('.', '_')
                dest_path = os.path.join(output_dir, f"playwright_{safe_name}.pdf")
                
                # Check for meta tag citation_pdf_url
                meta_pdf = page.locator("meta[name='citation_pdf_url']").get_attribute("content")
                if meta_pdf:
                    print(f"Found meta PDF URL: {meta_pdf}")
                    page.goto(meta_pdf)
                    page.wait_for_timeout(5000)
                    
                # Try to find a PDF link (very simplified example)
                pdf_locator = page.locator("a:has-text('PDF'), a[title*='PDF'], a[href$='.pdf'], button:has-text('Download')").first
                
                if pdf_locator.count() > 0:
                    print(f"Found PDF link for {doi}, attempting download...")
                    with page.expect_download(timeout=30000) as download_info:
                        pdf_locator.click()
                    download = download_info.value
                    download.save_as(dest_path)
                    print(f"✅ Downloaded to: {dest_path}")
                else:
                    print(f"⚠️ Could not find a direct PDF link for {doi} on the page.")
            except Exception as e:
                print(f"Failed to process {doi}: {e}")
                
        page.close()
        browser.close()
    except Exception as e:
        print(f"❌ Failed to connect or execute via Playwright: {e}")
        print("Note: If Chrome returns 400 or refuses connection, you MUST launch Chrome with:")
        print("  --remote-debugging-port=9222 --remote-debugging-address=0.0.0.0")
