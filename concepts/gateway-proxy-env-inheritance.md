---
title: "Gateway 代理环境继承问题"
created: 2026-04-23
modified: 2026-04-23
type: concept
tags: [agent, inference, tool-use, experiment]
---

# Gateway 代理环境继承问题

指在 shell 中已经设置代理变量，但 Hermes gateway 仍无法稳定访问外部模型，出现重试/超时的现象。

## 典型现象

- 终端里模型调用正常
- gateway 通道出现：`Retrying in ... (attempt x/3)` 或 `Max retries exhausted ...`
- 用户误以为是消息平台（如 Feishu）故障

## 根因

gateway 以守护进程形式运行时，不会自动继承当前交互 shell 的代理变量。也就是说：

- `proxy-on` 只影响当前 shell
- systemd 启动的服务拥有自己的环境
- 未做服务级注入时，gateway 可能仍走直连

## 解决方案

使用 systemd drop-in 做“服务级代理热插拔”：

1. 开启：写入 gateway 服务 drop-in 的 `Environment=` 变量
2. 关闭：移除 drop-in
3. 每次切换后执行 `daemon-reload + restart`
4. 通过进程环境与日志双重验证

## 验证标准

- 进程环境可见代理变量（大小写都检查）
- 重试风暴显著下降
- 消息通道恢复稳定

## 方法价值

该方案把代理控制从“人工记忆 + 临时命令”升级为“服务级、可观测、可回滚”的机制，适合作为长期运维基线。

## 相关页面

- [[hermes-docker-proxy-connectivity-source|Hermes + Docker 代理连通性（来源摘要）]]
- [[docker-proxy-listen-scope|Docker 代理监听范围问题]]
- [[llm-wiki-pattern|LLM Wiki模式]]
