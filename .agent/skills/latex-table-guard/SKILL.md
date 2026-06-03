---
name: latex-table-guard
description: 生成、修改或审查论文/学位论文中的 LaTeX 表格，尤其适用于双栏论文、IEEE/RA-L 风格文稿、自动生成的 .tex 表格片段和 PDF 编译日志中的 Overfull hbox 问题。创建 table/tabular/tabularx/longtable、编辑输出 LaTeX 表格的脚本、修复表格超出栏宽/页宽、验证生成 PDF 中表格不越界且流水线重跑不回退时使用。
---

# LaTeX 表格防溢出

## 目标

确保 LaTeX 表格位于目标栏宽或页宽内，包括由 Python/R/Julia/报告脚本自动生成的表格。除非用户明确要求改内容，否则只调整版式，不改数据、标题含义和引用标签。

## 工作流程

1. 确认表格来源。
   - 静态表格：修改对应 `.tex` 章节文件。
   - 自动生成表格：修改生成脚本并重新生成 `.tex`。不要只改生成物，否则下一次流水线会覆盖修复。

2. 将表号映射到 label 和文件。
   - 需要确认 Table 编号时查 `.aux`：`rg -n "newlabel\\{tab:|contentsline \\{table\\}" path/to/*.aux`。
   - 需要定位真实溢出时查日志：`rg -n -F "Overfull \\hbox" path/to/*.log`。
   - 结合日志中的 include 行，例如 `(./sections/table_ii.tex)`，判断附近 overfull 属于哪个表格。

3. 修改生成脚本或代码符号前遵守仓库规则。
   - 如果仓库要求影响分析，先对将编辑的函数/类运行 impact analysis。
   - 若风险为 HIGH 或 CRITICAL，先向用户说明影响面再继续。

4. 在 `tabular` 层做宽度保护。
   - `caption` 和 `label` 保持在 `resizebox` 外。
   - 双栏文稿中的普通 `table` 优先使用 `\columnwidth`。
   - 只有刻意跨双栏的 `table*` 才使用 `\textwidth`。
   - 确认主文件已加载 `graphicx`，因为 `\resizebox` 来自该宏包。

5. 重新生成并验证。
   - 修改生成脚本后必须重跑脚本。
   - 使用项目标准命令编译 PDF。
   - 重新检查日志，确认目标表格不再出现 overfull。
   - 对生成脚本运行语法检查，例如 `python3 -m py_compile ...`。
   - 运行 `git diff --check`；如果项目使用 GitNexus，提交前运行 detect-changes。

## 默认模板

双栏文稿中的单栏浮动表：

```latex
\begin{table}[t]
\centering
\caption{...}
\label{tab:...}
\small
\resizebox{\columnwidth}{!}{%
\begin{tabular}{lcccc}
\hline
... \\
\hline
\end{tabular}%
}
\end{table}
```

跨双栏全宽表：

```latex
\begin{table*}[t]
\centering
\caption{...}
\label{tab:...}
\small
\resizebox{\textwidth}{!}{%
\begin{tabular}{lcccccc}
...
\end{tabular}%
}
\end{table*}
```

Python 生成脚本中的列表模板：

```python
lines = [
    '\\begin{table}[t]',
    '\\centering',
    '\\caption{...}',
    '\\label{tab:...}',
    '\\small',
    '\\resizebox{\\columnwidth}{!}{%',
    '\\begin{tabular}{lcccc}',
    ...,
]
lines.extend(['\\hline', '\\end{tabular}%', '}', '\\end{table}', ''])
```

## 不要盲目缩放的情况

- 如果表本身不宽，只是单元格有长文本，优先使用 `p{...}`、`tabularx` 或缩短表头，而不是整体缩放。
- 如果表格行数很多，考虑 `longtable`、附录或补充材料，不要把正文表格缩得不可读。
- 如果溢出来自代码、JSON、URL、路径或目录树，应按文本/verbatim 换行问题处理，不要误判为表格仍越界。

## 生成脚本常见陷阱

- 避免用 `r"\\caption\{([^}]+)\}"` 这类简单正则解析 caption；`$\tau_{B2}$` 这种数学表达式包含嵌套花括号，会被截断。应使用平衡花括号解析，或从元数据中提取需要的信息。
- 如果脚本同时输出英文和本地化表格，必须同步修改两份输出并重跑脚本。
- 保留生成 `.tex` 中的 auto-generated 注释；长期有效的修复应落在生成脚本中。

## 可移植使用

在其它项目克隆或终端中使用时，复制整个目录：

```bash
mkdir -p ~/.codex/skills
cp -a .agent/skills/latex-table-guard ~/.codex/skills/
```

该目录是自包含的：`SKILL.md` 是运行时必需文件，`agents/openai.yaml` 仅提供 UI 元数据。

## 收尾汇报清单

完成任务时汇报：

- 已保护的表号、label 和文件。
- 已修改的生成脚本。
- PDF 构建命令和生成的 PDF 路径。
- 目标表格是否仍有 `Overfull \hbox`。
- 若仍有 overfull，说明它是否来自 JSONL、目录树、长路径或 verbatim 块等非表格内容。
