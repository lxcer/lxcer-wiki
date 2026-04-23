# Personal Knowledge Base - Lite Workflow

这是你的简化版 Wiki 管理规范。目标是：**最少操作、持续积累、低维护成本**。

---

## 1) 你只需要做的 3 件事

### A. 摄取新资料（Ingest）
你只要说一句：

`处理 raw/articles/xxx.md`

我会自动完成：
1. 创建/更新 1 个来源页（`wiki/sources/`）
2. 更新 1-3 个最相关概念页（`wiki/concepts/`）
3. 补齐交叉链接
4. 更新 `wiki/index.md` 和 `wiki/log.md`

### B. 日常提问（Query）
你只要说一句：

`基于 wiki 回答：<你的问题>`

我会自动完成：
1. 检索相关页面
2. 给出综合答案（带页面引用）
3. 若答案有长期价值，自动落地到 `wiki/synthesis/`

### C. 健康巡检（Lint）
你只要说一句：

`检查 wiki 健康状况`

我会自动完成：
1. 找孤儿页（无入链）
2. 找缺失页（被链接但不存在）
3. 找同名冲突（同 basename）
4. 校验 `index/log` 一致性
5. 直接修复可自动修复的问题

---

## 2) 精简目录约定

```
raw/                     # 原始资料（只读）
  articles/
  books/
  podcasts/
  videos/
  images/
  assets/

wiki/
  index.md               # 总目录（必须保持最新）
  log.md                 # 操作日志（必须追加记录）
  sources/               # 每个来源 1 页
  concepts/              # 稳定概念页
  entities/              # 可选：人物/组织（按需）
  synthesis/             # 可选：高价值综合结论
  drafts/                # 临时草稿
```

---

## 3) 页面最小模板（MVP）

所有页面都用这个最小结构，避免过度设计。

```markdown
---
title: "Page Title"
created: YYYY-MM-DD
modified: YYYY-MM-DD
type: [source|concept|entity|synthesis|index]
tags: [tag1, tag2]
---

# Page Title

一句话摘要。

## Key Points
- 要点 1
- 要点 2
- 要点 3

## Related
- [[related-page-a]]
- [[related-page-b]]

## Sources
- raw/... 或 [[source-page]]
```

---

## 4) 自动化规则（默认执行）

每次 Ingest 时默认遵循：
1. **只做必要更新**：来源页 + 最多 3 个关联页，避免一次改太多
2. **先连通再扩展**：新页至少 2 个 `[[wikilink]]`
3. **命名优先稳定**：kebab-case，避免重名
4. **索引和日志强制更新**：每次都更新 `index.md` 和 `log.md`
5. **不重复造页**：已有页面优先更新，不新建重复概念

---

## 5) 文件命名规范（保留）

- 文件名：`kebab-case.md`
- 人物：`firstname-lastname.md`
- 组织：`openai.md` 这类短名
- 概念：`descriptive-concept-name.md`
- 日期仅在必要时加入：`2026-04-23-topic.md`

---

## 6) 标签规则（简化）

仅保留两层标签，减少维护负担：

- 状态：`draft`, `in-progress`, `complete`
- 领域：`ai`, `business`, `psychology`, `science`, `philosophy`

不再强制细粒度标签；需要时再补。

---

## 7) 周期维护（超轻量）

每周执行一次：

1. `检查 wiki 健康状况`
2. 自动修复后，只人工确认两件事：
   - 新链接是否符合你的思路
   - 是否需要新增 1 个 synthesis 页

月末执行一次：

1. 清空/归档 `wiki/drafts/`
2. 看 `index.md` 是否仍好导航（不顺手就重排）

---

## 8) 你可以直接复制的指令

- `处理 raw/articles/xxx.md`
- `处理 raw/books/xxx.md，并重点关注商业模式`
- `基于 wiki 回答：OpenAI 与 Anthropic 产品路线有何分歧？`
- `把上一个回答沉淀为 synthesis 页面`
- `检查 wiki 健康状况并自动修复`

---

## 9) 成功标准（简版）

系统健康就看 4 个数：
1. 缺失链接 = 0
2. 孤儿页 = 0
3. 同名冲突 = 0
4. 每次 ingest 都有 log 记录

---

*Last updated: 2026-04-23*
*原则：先可持续，再完美。*
