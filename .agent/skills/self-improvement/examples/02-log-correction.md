# 示例 2：记录用户纠正

## 场景

Agent 生成了使用 `axios` 的 HTTP 请求代码，用户纠正说项目统一使用原生 `fetch` API。

## 输入

用户说："不要用 axios，我们这个项目统一用 fetch。"

## 输出

Agent 在 `.learnings/LEARNINGS.md` 末尾追加以下条目：

```markdown
## [LRN-20260323-001] correction

**Logged**: 2026-03-23T11:00:00+08:00
**Priority**: high
**Status**: pending
**Area**: frontend

### 摘要
项目 HTTP 请求统一使用 fetch API，不使用 axios

### 详情
在生成 API 调用代码时使用了 axios 库。用户纠正指出项目的 HTTP 请求约定
统一使用原生 fetch API，不引入第三方 HTTP 客户端。

### 建议操作
1. 在本项目中生成 HTTP 请求代码时统一使用 fetch
2. 此为全项目约定，应晋升到 AGENTS.md

### 元数据
- 来源: user_feedback
- 相关文件: src/api/
- 标签: HTTP, fetch, 项目约定

---
```

## 后续操作

由于这是全项目约定（跨多文件适用），Agent 应将其晋升到 `AGENTS.md`：

```markdown
## HTTP 请求
- 统一使用原生 fetch API，不使用 axios 等第三方库
```

并更新原条目状态为 `promoted`。
