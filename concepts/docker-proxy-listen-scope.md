---
title: "Docker 代理监听范围问题"
created: 2026-04-23
modified: 2026-04-23
type: concept
tags: [inference, tool-use, experiment]
---

# Docker 代理监听范围问题

指代理服务在容器内可用，但宿主机访问同一端口失败的一类问题。最常见于代理只绑定回环地址（127.0.0.1）时，端口映射看起来存在但实际不可用。

## 典型现象

- 容器内 `curl --proxy ...` 成功
- 宿主机 `curl --proxy ...` 失败
- 排查时容易误判为“节点失效”，实际是监听范围配置问题

## 根因模型

该问题本质不是“代理协议错误”，而是“监听地址作用域”错误：

1. 服务仅监听容器内回环地址，无法被宿主机转发流量命中
2. Docker 端口映射存在但无有效后端监听
3. 重启未加载新配置，导致“改了但没生效”的错觉

## 解决原则

1. 明确代理端口监听范围（目标是宿主机可达）
2. 同时检查端口映射与实际监听
3. 变更后执行重建/重启并重新验证
4. 用“容器内 + 宿主机”双侧测试作为验收标准

## 验证闭环

- 代理容器状态正常
- 端口映射存在
- 宿主机代理请求可达
- 出口行为符合预期

## 与 Hermes 场景的关系

该问题是上游前置问题：
- 如果这里未修复，后续 [[gateway-proxy-env-inheritance|gateway 代理注入]] 做得再好，模型请求也会失败。

## 相关页面

- [[hermes-docker-proxy-connectivity-source|Hermes + Docker 代理连通性（来源摘要）]]
- [[gateway-proxy-env-inheritance|Gateway 代理环境继承问题]]
- [[incremental-knowledge-building|增量知识构建]]
