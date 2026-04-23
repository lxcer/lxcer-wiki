---
title: "Wiki 操作日志"
created: 2026-04-14
modified: 2026-04-23
type: index
tags: [log, operations, maintenance]
---

# Wiki 操作日志

按时间顺序记录所有对Wiki的修改操作。

---

## [2026-04-23] ingest | Hermes + Docker 代理教程

**来源**: `raw/articles/hermes-gateway-proxy-hotplug-practice-2026-04-22.md`

**操作内容**:
1. 重新按修改后原文提取，不引入已删除段落
2. 新增来源摘要页：`sources/hermes-docker-proxy-connectivity-source.md`
3. 新增概念页：
   - `concepts/docker-proxy-listen-scope.md`
   - `concepts/gateway-proxy-env-inheritance.md`
4. 更新索引 `index.md`：补充新页面与统计

**结果**:
- 将工程教程沉淀为可复用的“问题模型 + 解法模型”知识节点
- 与既有页面形成双向链接，支持后续 query/lint 复用

---


## [2026-04-23] lint | wiki-health-auto-fix

**来源**: 健康检查与自动修复

**操作内容**:
1. 重命名来源摘要页面 `wiki/sources/llm-wiki-pattern.md` → `wiki/sources/llm-wiki-pattern-source.md`，消除同名冲突
2. 批量修复来源链接，统一指向 `[[llm-wiki-pattern-source]]`
3. 新建缺失概念页面:
   - `wiki/concepts/second-brain.md`
   - `wiki/concepts/knowledge-graph.md`
   - `wiki/concepts/zettelkasten.md`
   - `wiki/concepts/digital-garden.md`
   - `wiki/concepts/compounding-knowledge.md`
4. 更新索引页面 `wiki/index.md`，补充新页面并修正统计
5. 为 `wiki/index.md` 与 `wiki/log.md` 补齐 frontmatter

**结果**:
- 消除 `[[llm-wiki-pattern]]` 歧义链接
- 缺失概念页由 5 降为 0
- 索引完整性保持一致

---

## [2026-04-14] ingest | LLM Wiki模式

**来源**: `raw/llm-wiki.md`

**操作内容**:
1. 创建来源摘要页面 `wiki/sources/llm-wiki-pattern-source.md`
2. 创建概念页面 `wiki/concepts/llm-wiki-pattern.md`
3. 创建概念页面 `wiki/concepts/personal-knowledge-base.md`
4. 创建概念页面 `wiki/concepts/incremental-knowledge-building.md`
5. 创建/更新索引 `wiki/index.md`
6. 创建/更新日志 `wiki/log.md`

**要点**:
- LLM Wiki模式是区别于RAG的个人知识库方法论
- 三层架构: Raw(原始来源) → Wiki(LLM维护) → Schema(配置)
- 核心洞察: LLM承担维护负担，人类专注策划和思考
- 三个工作流程: Ingest(摄取)、Query(查询)、Lint(清理)
- 与Vannevar Bush的Memex愿景一脉相承

**创建的页面**:
- [[llm-wiki-pattern-source]] (来源摘要)
- [[llm-wiki-pattern]] (概念)
- [[personal-knowledge-base]]
- [[incremental-knowledge-building]]

---

*日志格式: `## [YYYY-MM-DD] operation-type | description`*
*操作类型: ingest(摄取) | query(查询) | lint(清理) | update(更新)*
