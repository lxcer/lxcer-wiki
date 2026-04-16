# Wiki Schema

## Domain
个人AI产品信息、AI相关研究笔记及知识库。记录AI产品、模型、技术、产品经验和研究发现。

## Conventions
- File names: lowercase, hyphens, no spaces (e.g., `claude-3-opus.md`)
- Every wiki page starts with YAML frontmatter (see below)
- Use `[[wikilinks]]` to link between pages (minimum 2 outbound links per page)
- When updating a page, always bump the `updated` date
- Every new page must be added to `index.md` under the correct section
- Every action must be appended to `log.md`

## Frontmatter
```yaml
---
title: Page Title
created: YYYY-MM-DD
updated: YYYY-MM-DD
type: entity | concept | comparison | query | summary
tags: [from taxonomy below]
sources: [raw/articles/source-name.md]
contradictions: []
---
```

## Tag Taxonomy
Every tag on a page must appear in this taxonomy. Add new tags here BEFORE using them.

### Products & Models
- ai-product: AI产品
- llm: 大语言模型
- multimodal: 多模态模型
- diffusion: 扩散模型
- foundation-model: 基础模型
- open-source: 开源模型

### Companies & Organizations
- company: 公司/组织
- lab: 研究机构
- startup: 创业公司

### Technology
- architecture: 模型架构
- training: 训练技术
- fine-tuning: 微调
- inference: 推理优化
- alignment: 对齐技术
- agent: AI Agent
- rag: 检索增强生成
- tool-use: 工具使用

### Product Development
- product: 产品开发
- product-strategy: 产品战略
- user-experience: 用户体验
- monetization: 商业化
- go-to-market: 市场推广

### Research
- research: 研究方向
- paper: 论文总结
- idea: 创意想法
- experiment: 实验结果
- survey: 调研

### Meta
- comparison: 对比分析
- timeline: 时间线
- controversy: 争议讨论
- prediction: 预测

## Page Thresholds
- **Create a page** when an entity/concept appears in 2+ sources OR is central to one source
- **Add to existing page** when a source mentions something already covered
- **DON'T create a page** for passing mentions, minor details, or things outside the domain
- **Split a page** when it exceeds ~200 lines — break into sub-topics with cross-links
- **Archive a page** when its content is fully superseded — move to `_archive/`, remove from index

## Entity Pages
One page per notable entity (AI models, companies, products, people). Include:
- Overview / what it is
- Key facts and dates
- Relationships to other entities ([[wikilinks]])
- Source references

## Concept Pages
One page per concept or topic. Include:
- Definition / explanation
- Current state of knowledge
- Open questions or debates
- Related concepts ([[wikilinks]])

## Comparison Pages
Side-by-side analyses. Include:
- What is being compared and why
- Dimensions of comparison (table format preferred)
- Verdict or synthesis
- Sources

## Update Policy
When new information conflicts with existing content:
1. Check the dates — newer sources generally supersede older ones
2. If genuinely contradictory, note both positions with dates and sources
3. Mark the contradiction in frontmatter: `contradictions: [page-name]`
4. Flag for user review in the lint report
