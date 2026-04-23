---
title: "LLM Wiki模式（来源摘要）"
created: 2026-04-14
modified: 2026-04-23
type: source
tags: [llm-wiki, personal-knowledge-base, knowledge-management, obsidian, second-brain]
---

# LLM Wiki模式（来源摘要）

一种使用LLM增量构建和维护个人知识库（Wiki）的方法论，区别于传统RAG的实时检索模式。

## 核心要点

- **持久化知识积累**: 不同于RAG每次重新检索，Wiki是持续更新的结构化知识库
- **三层架构**: 原始来源（immutable）→ Wiki（LLM维护）→ Schema（配置规范）
- **双向维护**: 人类负责策划和提问，LLM负责所有的维护工作（交叉引用、一致性、更新）
- **复合增长**: 每添加一个来源可能更新10-15个页面，知识网络自动扩展

## 关键概念

- [[llm-wiki-pattern|LLM Wiki模式]] - 核心方法论
- [[personal-knowledge-base|个人知识库]] - 知识体系架构
- [[incremental-knowledge-building|增量知识构建]] - 渐进式积累策略

## 工作流程

1. **Ingest（摄取）**: 添加来源 → LLM读取 → 讨论要点 → 创建/更新页面 → 更新索引
2. **Query（查询）**: 搜索页面 → 合成答案 → 可选择将答案归档为新页面
3. **Lint（清理）**: 定期检查矛盾、孤立页面、缺失交叉引用

## 技术栈

- **Obsidian**: 推荐的Wiki浏览工具（图谱视图、反向链接、Dataview插件）
- **Git**: 版本控制
- **Obsidian Web Clipper**: 浏览器剪藏
- **可选**: qmd（本地搜索引擎）

## 启发来源

**Vannevar Bush的Memex（1945）**: 个人化、策展化的知识存储，强调文档间的关联路径（associative trails）。LLM Wiki解决了Bush未能解决的问题——谁来做维护工作。

## 重要引用

> "The tedious part of maintaining a knowledge base is not the reading or the thinking — it's the bookkeeping."

> "Humans abandon wikis because the maintenance burden grows faster than the value. LLMs don't get bored, don't forget to update a cross-reference, and can touch 15 files in one pass."

## 相关资源

- 原始文档: `raw/llm-wiki.md`
- 项目仓库: 本地个人知识库
- 当前配置: `AGENTS.md`

## 标签

#llm-wiki #personal-knowledge-base #knowledge-management #obsidian #second-brain
