import sys
import os

# Add the MCP server directory to sys.path so we can import it
mcp_dir = os.path.abspath('/root/work/paper1/.agent/mcp-servers/scholar-downloader')
sys.path.append(mcp_dir)

# Modify the dotenv path dynamically for the current run if needed,
# though it's hardcoded in server.py, we can just run it.
from server import download_papers_via_browser

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

def _wsl_windows_host() -> str:
    """WSL2 访问 Windows 宿主机时，127.0.0.1 指向 Linux 自身，需用网关 IP。"""
    try:
        with open('/etc/resolv.conf', encoding='utf-8') as f:
            for line in f:
                if line.startswith('nameserver '):
                    return line.split()[1].strip()
    except OSError:
        pass
    return '127.0.0.1'


debug_host = os.environ.get('CHROME_DEBUG_HOST', _wsl_windows_host())
print(f"Calling download_papers_via_browser (host={debug_host}:9222)...")
result = download_papers_via_browser(
    dois=dois,
    output_dir='/root/work/paper1/doctor/paper1/data/papers',
    debug_port=9222,
    debug_host=debug_host,
)

print("\n--- Result ---")
print(result)
