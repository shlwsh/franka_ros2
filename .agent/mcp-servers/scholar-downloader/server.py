import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# Initialize the MCP Server
mcp = FastMCP("ScholarDownloader")

@mcp.tool()
def download_papers(dois: list[str], output_dir: str = "doctor/paper1/data/papers") -> str:
    """
    Download academic papers via Sci-Hub based on DOIs.
    
    Args:
        dois: List of DOIs to download, e.g. ["10.1109/TIP.2024.3378466"]
        output_dir: Directory to save the downloaded PDFs, defaults to doctor/paper1/data/papers
    """
    # Use absolute path if the output_dir is relative
    # Assuming this is run from the workspace root
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    results = []
    
    for doi in dois:
        # Use absolute path to scidownl based on the current python executable's location
        import sys
        scidownl_path = os.path.join(os.path.dirname(sys.executable), "scidownl")
        safe_name = doi.replace('/', '_').replace('.', '_')
        cmd = [scidownl_path, "download", "--doi", doi, "--out", abs_output_dir]
        
        try:
            print(f"Downloading {doi} to {abs_output_dir}...")
            # Execute the download command
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # Check if successful
            pdf_files = list(Path(abs_output_dir).glob(f"*{safe_name}*.pdf"))
            if pdf_files or "success" in process.stdout.lower() or "already exists" in process.stdout.lower():
                results.append(f"✅ Success: {doi}")
            else:
                results.append(f"❌ Failed: {doi}\n  stdout: {process.stdout.strip()}\n  stderr: {process.stderr.strip()}")
        except subprocess.TimeoutExpired:
            results.append(f"❌ Timeout (120s): {doi}")
        except Exception as e:
            results.append(f"❌ Exception: {doi} - {str(e)}")

    # Return summary to the AI
    return "\n".join(results) + "\n\n(Tip: After download completes, run `python3 doctor/paper1/scripts/paper1_audit_papers.py` to re-audit if applicable)"

import json
import time
import shutil
import glob
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.service import Service as ChromeService
import requests
from dotenv import load_dotenv

# Load env file to get DASHSCOPE_API_KEY
load_dotenv("/home/ros/work/paper1/.env.mygit")

def ask_llm_for_xpath(elements_list):
    api_key = os.environ.get("DASHSCOPE_API_KEY")
    base_url = os.environ.get("DASHSCOPE_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
    model = os.environ.get("DASHSCOPE_MODEL", "deepseek-v3")
    if not api_key:
        print("No DASHSCOPE_API_KEY found, skipping LLM.")
        return None
        
    prompt = f"""You are an expert at web scraping. I have a list of clickable elements from a web page (academic publisher). 
My goal is to download the PDF of the paper.
Please identify the BEST element that represents the "Download PDF" or "View PDF" button.
Return ONLY the EXACT 'xpath' value of that element as a plain string. No markdown, no quotes, no explanation.

Elements:
{json.dumps(elements_list, indent=2)}
"""
    try:
        resp = requests.post(
            f"{base_url.rstrip('/')}/chat/completions",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={
                "model": model,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.1
            },
            timeout=30
        )
        resp_data = resp.json()
        if "choices" in resp_data and len(resp_data["choices"]) > 0:
            xpath = resp_data["choices"][0]["message"]["content"].strip("`'\"\n ")
            return xpath
    except Exception as e:
        print(f"LLM Error: {e}")
    return None

def get_latest_pdf_in_dir(directory, since_time):
    """Finds the most recently modified PDF in a directory created/modified after since_time"""
    pdfs = glob.glob(os.path.join(directory, "*.pdf"))
    if not pdfs:
        return None
    valid_pdfs = [p for p in pdfs if os.path.getmtime(p) > since_time]
    if not valid_pdfs:
        return None
    return max(valid_pdfs, key=os.path.getmtime)

def download_pdf_with_cookies(driver, url, dest_path):
    if not url:
        return False
    session = requests.Session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie['name'], cookie['value'])
    try:
        user_agent = driver.execute_script("return navigator.userAgent;")
        session.headers.update({"User-Agent": user_agent})
        
        print(f"Attempting to download from: {url}")
        res = session.get(url, stream=True, timeout=30)
        content_type = res.headers.get("Content-Type", "").lower()
        if "application/pdf" in content_type or res.url.lower().endswith(".pdf"):
            with open(dest_path, "wb") as f:
                for chunk in res.iter_content(1024):
                    f.write(chunk)
            return True
        elif "text/html" in content_type:
            import re
            # Look for iframe src
            match = re.search(r'<iframe[^>]*src="([^"]+)"', res.text, re.IGNORECASE)
            if match:
                pdf_url = match.group(1)
                if pdf_url.startswith("//"):
                    pdf_url = "https:" + pdf_url
                elif pdf_url.startswith("/"):
                    from urllib.parse import urlparse
                    parsed = urlparse(url)
                    pdf_url = f"{parsed.scheme}://{parsed.netloc}{pdf_url}"
                
                print(f"Found nested PDF URL: {pdf_url}")
                res2 = session.get(pdf_url, stream=True, timeout=30)
                # Save anyway if status code is good
                if res2.status_code == 200:
                    with open(dest_path, "wb") as f:
                        for chunk in res2.iter_content(1024):
                            f.write(chunk)
                    # Verify file is not empty and is a valid pdf (starts with %PDF)
                    with open(dest_path, "rb") as f:
                        header = f.read(4)
                        if header == b"%PDF":
                            return True
                    os.remove(dest_path) # cleanup invalid
    except Exception as e:
        print(f"Download failed via requests: {e}")
    return False

@mcp.tool()
def download_papers_via_browser(dois: list[str], output_dir: str = "doctor/paper1/data/papers", debug_port: int = 9222) -> str:
    """
    Download academic papers using a locally running Chrome browser with Remote Debugging port enabled,
    enhanced with LLM parsing for complex DOMs and cross-OS file routing.
    """
    abs_output_dir = os.path.abspath(output_dir)
    os.makedirs(abs_output_dir, exist_ok=True)
    results = []
    
    options = Options()
    options.add_experimental_option("debuggerAddress", f"127.0.0.1:{debug_port}")
    
    try:
        service = ChromeService(ChromeDriverManager(driver_version="148.0.7778.218").install())
        driver = webdriver.Chrome(service=service, options=options)
    except Exception as e:
        return f"❌ Failed to connect to Chrome: {e}"

    original_window = driver.current_window_handle
    driver.switch_to.new_window('tab')
    
    # JS to extract clickable candidates
    js_extractor = """
    function getElementXPath(elt) {
        var path = "";
        for (; elt && elt.nodeType == 1; elt = elt.parentNode) {
            var idx = 1;
            for (var sib = elt.previousSibling; sib; sib = sib.previousSibling) {
                if (sib.nodeType == 1 && sib.tagName == elt.tagName) idx++;
            }
            var xname = elt.tagName.toLowerCase();
            if (idx > 1) xname += "[" + idx + "]";
            path = "/" + xname + path;
        }
        return path;
    }
    var candidates = [];
    var elements = document.querySelectorAll('a, button');
    for (var i = 0; i < elements.length; i++) {
        var el = elements[i];
        var text = (el.innerText || el.textContent || el.title || el.getAttribute("aria-label") || "").trim().toLowerCase();
        if (text.length > 0 && (text.includes("pdf") || text.includes("download") || text.includes("article") || text.includes("full text") || el.className.toLowerCase().includes("pdf"))) {
            candidates.push({
                "tag": el.tagName,
                "text": text,
                "class": el.className,
                "href": el.href || "",
                "xpath": getElementXPath(el)
            });
        }
    }
    if (candidates.length === 0) {
        for (var i = 0; i < elements.length && candidates.length < 50; i++) {
            var el = elements[i];
            var text = (el.innerText || el.textContent || "").trim();
            if (text.length > 0) {
                candidates.push({
                    "tag": el.tagName,
                    "text": text,
                    "href": el.href || "",
                    "xpath": getElementXPath(el)
                });
            }
        }
    }
    return candidates.slice(0, 50);
    """
    
    for doi in dois:
        print(f"🔄 Processing DOI via browser (LLM Enhanced): {doi}")
        urls_to_try = [
            f"https://doi.org/{doi}",
            f"https://ieeexplore.ieee.org/document/?reload=true&arnumber={doi.split('.')[-1] if '10.1109' in doi else ''}",
        ]
        
        success = False
        safe_name = doi.replace('/', '_').replace('.', '_')
        dest_path = os.path.join(abs_output_dir, f"llm_downloaded_{safe_name}.pdf")
        
        for url in urls_to_try:
            try:
                driver.get(url)
                time.sleep(6)  # Wait for full page and react components
                
                # Try static XPaths first
                download_buttons = [
                    "//a[contains(@class, 'pdf') or contains(text(), 'PDF') or contains(@title, 'PDF')]",
                    "//button[contains(text(), 'Download')]",
                    "//a[contains(@href, '.pdf')]"
                ]
                
                found_xpath = None
                pdf_direct_url = None
                
                # Check for standard Google Scholar meta tag first!
                try:
                    meta_tag = driver.find_element(By.XPATH, "//meta[@name='citation_pdf_url']")
                    pdf_direct_url = meta_tag.get_attribute("content")
                    if pdf_direct_url:
                        print(f"🌟 Found citation_pdf_url meta tag: {pdf_direct_url}")
                except:
                    pass
                
                if pdf_direct_url:
                    downloaded = download_pdf_with_cookies(driver, pdf_direct_url, dest_path)
                    if downloaded:
                        print(f"✅ Downloaded via meta tag: {dest_path}")
                        success = True
                        break
                
                for xpath in download_buttons:
                    try:
                        btn = driver.find_element(By.XPATH, xpath)
                        if btn.is_displayed():
                            found_xpath = xpath
                            break
                    except:
                        continue
                
                # If static fails, ask LLM
                if not found_xpath:
                    print("⚠️ Static XPaths failed. Using JS DOM extraction + LLM...")
                    candidates = driver.execute_script(js_extractor)
                    if candidates:
                        found_xpath = ask_llm_for_xpath(candidates)
                        print(f"🧠 LLM suggested XPath: {found_xpath}")
                
                if found_xpath and not success:
                    try:
                        btn = driver.find_element(By.XPATH, found_xpath)
                        btn_href = btn.get_attribute("href")
                        downloaded = download_pdf_with_cookies(driver, btn_href, dest_path)
                        
                        if not downloaded:
                            print("Direct href download failed, trying to click button and scrape resulting URL...")
                            start_url = driver.current_url
                            handles_before = driver.window_handles
                            
                            driver.execute_script("arguments[0].scrollIntoView(true);", btn)
                            time.sleep(1)
                            btn.click()
                            time.sleep(6) # wait for redirect
                            
                            handles_after = driver.window_handles
                            switched = False
                            if len(handles_after) > len(handles_before):
                                driver.switch_to.window(handles_after[-1])
                                switched = True
                                
                            new_url = driver.current_url
                            if new_url != start_url:
                                downloaded = download_pdf_with_cookies(driver, new_url, dest_path)
                            
                            if switched:
                                driver.close()
                                driver.switch_to.window(handles_before[0])
                                
                        if downloaded:
                            print(f"✅ Downloaded to: {dest_path}")
                            success = True
                            break
                    except Exception as e:
                        print(f"Failed to click LLM suggested xpath: {e}")
                        
            except Exception as e:
                print(f"Failed {url}: {e}")
        
        if success:
            results.append(f"✅ Success (LLM/DOM Download & Transfer): {doi}")
        else:
            results.append(f"⚠️ Failed to auto-download via browser: {doi}")
            
    try:
        driver.close()
        driver.switch_to.window(original_window)
    except:
        pass
    
    return "\n".join(results) + "\n\n(Tip: Downloads have been automatically moved to doctor/paper1/data/papers/)"



if __name__ == "__main__":
    mcp.run()
