# 示例 3：晋升学习到项目记忆

## 场景

同一个配置相关的学习（Pattern-Key: `config.env_load_order`）已经出现 3 次，
跨 2 个不同任务，在 30 天内，满足自动晋升条件。

## 输入

Agent 检测到 `.learnings/LEARNINGS.md` 中的以下条目：

```markdown
## [LRN-20260310-002] knowledge_gap

...
- Pattern-Key: config.env_load_order
- Recurrence-Count: 3
- First-Seen: 2026-03-01
- Last-Seen: 2026-03-10
```

## 输出

### 步骤 1：在 AGENTS.md 中添加规则

```markdown
## 配置约定
- 环境变量加载顺序: .env.local > .env.{mode} > .env
- 不要覆盖 .env.local 中用户自定义的值
```

### 步骤 2：更新原学习条目

```markdown
**Status**: promoted
**Promoted**: AGENTS.md
```

### 步骤 3：添加解决记录

```markdown
### 解决记录
- **Resolved**: 2026-03-10T14:00:00+08:00
- **Notes**: 已晋升到 AGENTS.md 配置约定章节
```

## 晋升判断依据

满足自动晋升的三个条件：
1. ✅ `Recurrence-Count >= 3`（出现 3 次）
2. ✅ 跨 2 个不同任务
3. ✅ 在 30 天窗口内（3月1日 - 3月10日）
