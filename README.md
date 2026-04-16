# lxcer-wiki

个人AI产品信息、AI相关研究笔记及知识库。

基于 [Karpathy LLM Wiki](https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f) 模式构建，使用 interlinked markdown 文件作为持久知识库。

## 结构

```
wiki/
├── SCHEMA.md           # 模式定义和约定
├── index.md            # 内容目录
├── log.md              # 操作日志
├── raw/                # 原始源材料（只读）
│   ├── articles/       # 网络文章
│   ├── papers/         # 论文
│   ├── transcripts/    # 文字记录
│   └── assets/         # 图片/资源
├── entities/           # 实体页面（产品、模型、公司、人物）
├── concepts/           # 概念/主题页面
├── comparisons/        # 对比分析
└── queries/            # 有保留价值的查询结果
```

## 使用方式

这个 wiki 就是纯 markdown 文件，可以用任何编辑器打开。推荐配合 Obsidian 使用，`[[wikilinks]]` 原生支持。

## License

MIT
