# 个人知识库

基于 [llm-wiki.md](./llm-wiki.md) 模式构建的 LLM 驱动的个人知识库。

## 目录结构

```
.
├── AGENTS.md              # 主配置文件（简化流程、规范）
├── README.md              # 本文件
├── raw/                   # 原始资料（LLM 只读）
│   ├── articles/         # 文章、论文、博客
│   ├── books/            # 书籍笔记
│   ├── podcasts/         # 播客笔记
│   ├── videos/           # 视频笔记
│   ├── images/           # 截图、图表
│   ├── assets/           # 附件资源
│   └── llm-wiki.md       # LLM Wiki 模式文档
└── wiki/                  # Wiki 页面（LLM 生成）
    ├── index.md          # 内容索引
    ├── log.md            # 操作日志
    ├── sources/          # 资料摘要
    ├── entities/         # 人物、组织
    ├── concepts/         # 概念、理论
    ├── synthesis/        # 综合分析
    └── drafts/           # 草稿
```

## 使用方式

### 1. 添加原始资料

将文章、笔记等保存到 `raw/` 下的相应目录：

```bash
# 示例：保存一篇文章
wget -O raw/articles/my-article.md "https://example.com/article"
```

或使用 Obsidian Web Clipper 浏览器插件直接剪藏。

### 2. Ingest（处理资料）

告诉 Claude Code：

```
处理 raw/articles/my-article.md
```

Claude 将：
1. 读取并分析资料
2. 创建/更新 wiki 页面
3. 更新 `index.md` 和 `log.md`

### 3. 查看知识库

在 [Obsidian](https://obsidian.md/) 中：

1. 打开此文件夹作为 vault
2. 启用 Graph View 查看知识图谱
3. 使用 Quick Switcher 快速导航

## 核心文件说明

| 文件 | 用途 |
|------|------|
| `AGENTS.md` | 主配置文件，包含简化后的工作流程、命名规范、维护规则 |
| `wiki/index.md` | 内容索引，方便快速导航 |
| `wiki/log.md` | 操作日志，记录所有 ingest/query/update 操作 |
| `llm-wiki.md` | LLM Wiki 模式的原始文档 |

## 成功指标

你的知识库运行良好的标志：

- ✅ **积累性**：添加资料后知识库变得更丰富，而不只是更大
- ✅ **连接性**：大多数页面链接到多个其他页面，图谱显示密集网络
- ✅ **可检索性**：能在几秒内找到几个月前的信息
- ✅ **综合性**：wiki 包含任何单一来源中都没有的洞察
- ✅ **维护成本**：保持有序几乎不需要努力（由 LLM 完成）

---

*知识库初始化于 2026-04-13*
*配置详见 [AGENTS.md](./AGENTS.md)*
