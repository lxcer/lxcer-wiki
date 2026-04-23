---
title: "Hermes + Docker 代理连通性（来源摘要）"
created: 2026-04-23
modified: 2026-04-23
type: source
tags: [agent, inference, tool-use, survey]
---

# Hermes + Docker 代理连通性（来源摘要）

这篇来源给出了一套面向国内网络环境的可执行教程，目标是解决 Hermes 访问 GPT/Claude 等外部模型时的连通性问题，重点覆盖 Docker 代理部署、监听地址修正，以及 gateway 进程级代理注入。

## 核心结论

1. 仅完成 Docker 代理容器部署还不够，必须做“容器内 + 宿主机”双侧验证。
2. 常见故障是代理监听只在 `127.0.0.1:7890`，导致宿主机无法使用；需要修正为可对外监听（如 `0.0.0.0:7890`）。
3. gateway 属于守护进程，不会自动继承交互 shell 环境变量；需用 systemd drop-in 注入代理变量，才能缓解 `Retrying in ... (attempt x/3)`。

## 可复用流程

- 步骤1：基于 `mihomo-sub` 配置启动 Docker 代理
- 步骤2：验证代理可用性（容器内 + 宿主机）
- 步骤3：为 `hermes-gateway` 做服务级代理热插拔
- 步骤4：观察日志确认重试风暴是否下降

## 提炼出的关键问题

- [[docker-proxy-listen-scope|Docker 代理监听范围问题]]：为什么容器可用而宿主机不可用
- [[gateway-proxy-env-inheritance|Gateway 代理环境继承问题]]：为什么 `proxy-on` 后 gateway 仍然报重试
- [[llm-wiki-pattern|LLM Wiki模式]]：如何将实操经验沉淀成可检索资产而不是聊天记录

## 来源

- 原始文章：`raw/articles/hermes-gateway-proxy-hotplug-practice-2026-04-22.md`
- 参考项目：`https://github.com/pure-white-ice-cream/mihomo-sub`
