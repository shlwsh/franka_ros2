# 文献下载 MCP 服务（Scholar Downloader）技术实现方案

## 1. 背景与目标

当前项目已经存在 `scholar-search` Skill，主要解决基于 SerpApi/OpenAlex 的文献检索及开放获取（OA）PDF、arXiv 预印本的自动下载。但针对非 OA 的受限文献（如 IEEE、ACM、Springer 的付费论文），现有的方案依赖于人工介入或手动配置补齐。

为了完全自动化论文审计与归档工作流，结合已有的 `scidownl`、`PyPaperBot` 工具库，规划实现一个 **“专职负责突破下载限制的文献下载器（Scholar Downloader MCP）”**。
通过接入 Model Context Protocol (MCP)，将下载能力封装为标准化 Tool，使 Cursor/Claude 等 AI 助手能够自主传入 DOI 列表并完成下载闭环。

## 2. 工具选型与架构设计

### 2.1 核心下载引擎
- **首选引擎**：`scidownl`。支持最新的 Sci-Hub 域名自动更新，支持根据 DOI 稳定下载。
- **备选引擎**：`PyPaperBot`。支持 Google Scholar 结合 Sci-Hub 进行补充查询。
- **审计集成**：下载完成后自动提供已下载列表给 `doctor/paper1/scripts/paper1_audit_papers.py` 以进行数据对齐。

### 2.2 服务框架
使用 Python 官方的 `mcp` SDK (`mcp[cli]`) 构建 FastMCP 服务：
- **可扩展性**：基于 `@mcp.tool()` 装饰器，快速将 Python 下载函数暴露为大语言模型可用的工具。
- **独立性**：作为一个独立的 MCP Server 运行在本地，解决沙箱环境无网络限制或 IP 被封禁的问题。

## 3. 具体实现步骤

### 3.1 环境依赖与初始化
新建一个专门的 MCP 服务目录，例如 `.agent/mcp-servers/scholar-downloader/`。

```bash
# 依赖安装
pip install scidownl mcp
# 首次运行需要更新最新域名
scidownl domain.update
```

### 3.2 核心 MCP Server 代码结构 (`server.py`)

```python
import os
import subprocess
from pathlib import Path
from mcp.server.fastmcp import FastMCP

# 初始化 MCP Server
mcp = FastMCP("ScholarDownloader")

@mcp.tool()
def download_papers(dois: list[str], output_dir: str = "doctor/paper1/data/papers") -> str:
    """
    通过 Sci-Hub 等源根据 DOI 批量下载科研文献。
    
    Args:
        dois: 需要下载的论文 DOI 列表，如 ["10.1109/TIP.2024.3378466"]
        output_dir: 存放下载 PDF 的目录，默认为 paper1 项目的 data/papers/
    """
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for doi in dois:
        safe_name = doi.replace('/', '_').replace('.', '_')
        cmd = ["scidownl", "download", "--doi", doi, "--out", output_dir]
        
        try:
            # 执行下载命令
            process = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            # 校验是否成功
            pdf_files = list(Path(output_dir).glob(f"*{safe_name}*.pdf"))
            if pdf_files or "success" in process.stdout.lower():
                results.append(f"✅ 成功: {doi}")
            else:
                results.append(f"❌ 失败: {doi} - 请检查网络或是否有收录")
        except Exception as e:
            results.append(f"❌ 异常: {doi} - {str(e)}")

    # 汇总并返回给 AI 的执行结果
    return "\n".join(results) + "\n\n(提示: 下载完成后建议执行 python3 doctor/paper1/scripts/paper1_audit_papers.py 重新核验审计结果)"

if __name__ == "__main__":
    # 以 stdio 模式启动服务
    mcp.run()
```

### 3.3 客户端集成配置 (Cursor/IDE)

在 Cursor 的 `~/.cursor/mcp.json` 或本项目的 `.vscode/settings.json` 中添加该 MCP 服务器配置：

```json
{
  "mcpServers": {
    "scholar-downloader": {
      "command": "python3",
      "args": ["/home/ros/work/paper1/.agent/mcp-servers/scholar-downloader/server.py"]
    }
  }
}
```

## 4. 自动闭环工作流 (Agentic Workflow)

一旦上述 MCP Tool 部署成功，AI 可以实现如下自动化闭环：
1. **审计发现缺失**：AI 运行 `paper1_audit_papers.py` 或查看 `cite_audit.json`，发现有 X 篇文献（含 DOI）未本地归档 PDF。
2. **调用 MCP 下载**：AI 自动提取缺失的 DOI 列表，调用 `download_papers(dois=[...])` 工具。
3. **工具执行**：`scholar-downloader` MCP 在本地网络（需科学上网）中依次获取 PDF 并存入 `data/papers/`。
4. **重新审计**：AI 再次执行 `paper1_audit_papers.py`，确认所有引用的文献均已在本地对齐并生成审计报告。

## 5. 潜在问题与对策
- **网络限制**：Sci-Hub 的可访问性较差。如果直连失败，需要在 MCP 服务的 Python 环境或启动命令中注入代理（如 `export HTTP_PROXY=...`）。
- **反爬策略**：部分时候 `scidownl` 会遭遇验证码拦截，若出现连续失败，应当停止重试并反馈给人工，或引入 `PyPaperBot` 作为冗余方案。
- **文件命名标准化**：默认下载的文件名可能与项目的规范命名不同（`[年份]_[作者]_[简写标题].pdf`）。可以在下载成功后，调用已有 Skill (`scholar-search/scripts/download_missing_from_audit.py`) 内的函数对其进行重命名映射。
