# 示例 1：记录命令错误

## 场景

执行 `npm install` 失败，因为项目实际使用 bun 作为包管理器。

## 输入

Agent 运行 `npm install`，终端返回：

```
npm ERR! code ENOLOCK
npm ERR! This command requires an existing lockfile.
```

## 输出

Agent 在 `.learnings/ERRORS.md` 末尾追加以下条目：

```markdown
## [ERR-20260323-001] npm_install

**Logged**: 2026-03-23T10:30:00+08:00
**Priority**: medium
**Status**: pending
**Area**: config

### 摘要
npm install 失败，项目使用 bun 而非 npm

### 错误信息
```
npm ERR! code ENOLOCK
npm ERR! This command requires an existing lockfile.
```

### 上下文
- 执行的命令: npm install
- 项目根目录存在 bun.lockb
- 应使用 bun install

### 建议修复
检测到 bun.lockb 时使用 bun install，而非 npm install

### 元数据
- 可复现: yes
- 相关文件: bun.lockb, package.json
- 标签: 包管理器, bun, npm

---
```
