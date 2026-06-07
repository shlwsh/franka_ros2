import subprocess
import os
from pathlib import Path

def download_with_scidownl(doi, title, output_dir="doctor/paper1/data/papers"):
    os.makedirs(output_dir, exist_ok=True)
    print(f"\n🔄 下载: {title} ({doi})")
    
    # Use the absolute path to the venv's scidownl
    import sys
    scidownl_path = os.path.join("/home/ros/work/paper1/.agent/mcp-servers/scholar-downloader/.venv/bin", "scidownl")
    
    try:
        cmd = [scidownl_path, "download", "--doi", doi, "--out", output_dir]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
        print(result.stdout.strip())
        if result.stderr: 
            print("STDERR:", result.stderr.strip())
        
        # Check success
        if any(x in result.stdout.lower() for x in ["success", "saved", ".pdf", "already exists"]):
            print("✅ 成功")
            return True
    except Exception as e:
        print("❌ 异常:", e)
    return False

if __name__ == "__main__":
    papers = [
        ("10.1109/MRA.2011.2181749", "chitta2009moveit"),
        ("10.1016/j.cmpb.2014.10.001", "huang2015tcn"),
        # kang2017neurosurgeon already downloaded via wget
        ("10.1109/COMST.2019.2892586", "liu2019robotcloud"),
        ("10.1016/j.patcog.2016.01.017", "qi2016tongue"),
        # wang2014edge already downloaded via wget
        ("10.1109/TCSVT.2018.2866628", "zhang2018blind"),
        ("10.1007/s10462-019-09735-6", "zhang2020tongue"),
    ]
    
    for doi, key in papers:
        download_with_scidownl(doi, key)
