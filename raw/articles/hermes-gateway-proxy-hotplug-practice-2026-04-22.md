# hermes + docker代理：解决 hermes 国内无法连接 GPT/Claude 等问题

## 适用场景
- Hermes 在国内网络环境下访问外部模型（GPT/Claude 等）不稳定或超时
- 希望通过 Docker 部署代理，并且能随时开关，不影响正常上网

---

## 1. Docker 代理搭建（参考 mihomo-sub 开源项目）

参考项目：
- https://github.com/pure-white-ice-cream/mihomo-sub

实践建议：
- 重点只改你自己的订阅配置（如 `sub_url`）与更新策略（如 `cron`）

基础步骤：
```bash
# 在 mihomo-sub 项目目录中
docker compose up -d

docker compose ps
docker logs --tail=100 mihomo-sub
```

最小验证：
```bash
# 容器内验证
docker exec -it mihomo-sub sh -lc 'curl -sS --proxy http://127.0.0.1:7890 https://api.ipify.org && echo'

# 宿主机验证
curl -sS --proxy http://127.0.0.1:7890 https://api.ipify.org ; echo
```

---

## 2. 容器默认监听 127.0.0.1:7890，导致宿主机不可用：如何改为 0.0.0.0:7890

### 现象
- 容器内代理可用
- 宿主机 `curl --proxy http://127.0.0.1:7890 ...` 失败

### 原因
代理服务只监听容器回环地址（127.0.0.1），Docker 端口映射无法把这类监听正确暴露给宿主机访问。

### 修改方案
在 mihomo 配置里确认以下关键项：
```yaml
mixed-port: 7890
allow-lan: true
bind-address: 0.0.0.0
```

同时确认 compose 端口映射存在：
```yaml
ports:
  - "7890:7890"
  - "9090:9090"
```

应用变更：
```bash
docker compose down
docker compose up -d
```

验证：
```bash
docker port mihomo-sub
ss -lntp | grep 7890 || true
curl -sS --proxy http://127.0.0.1:7890 https://api.ipify.org ; echo
```

说明：
- 如果你改完配置仍然“容器内可用、宿主机不可用”，优先排查：端口映射是否生效、容器是否真的重启到新配置、防火墙策略。

---

## 3. Gateway客户端(如Feishu)连接报错Retrying

### 现象
通过飞书客户端访问hermes：
- `Retrying in ... (attempt x/3)...`
- `Max retries exhausted ...`

### 根因
Gateway 是守护进程（systemd user service），不会自动继承当前交互 shell 的代理环境变量。

### 解决方案（推荐）
用 systemd drop-in 给 `hermes-gateway` 单独注入代理环境变量，实现热插拔开关。

#### 4.1 开启 gateway 代理
```bash
mkdir -p ~/.config/systemd/user/hermes-gateway.service.d
cat > ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf <<'EOF'
[Service]
Environment=HTTP_PROXY=http://127.0.0.1:7890
Environment=HTTPS_PROXY=http://127.0.0.1:7890
Environment=ALL_PROXY=http://127.0.0.1:7890
Environment=NO_PROXY=localhost,127.0.0.1,::1
Environment=http_proxy=http://127.0.0.1:7890
Environment=https_proxy=http://127.0.0.1:7890
Environment=all_proxy=http://127.0.0.1:7890
Environment=no_proxy=localhost,127.0.0.1,::1
EOF

systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```

#### 4.2 关闭 gateway 代理
```bash
rm -f ~/.config/systemd/user/hermes-gateway.service.d/proxy.conf
systemctl --user daemon-reload
systemctl --user restart hermes-gateway
```

#### 4.3 检查是否生效
```bash
systemctl --user cat hermes-gateway.service | grep -E 'Environment=' || true

PID=$(pgrep -f 'python -m hermes_cli.main gateway run --replace' | head -1 || true)
[ -n "$PID" ] && tr '\0' '\n' < /proc/$PID/environ | grep -aiE '^(http_proxy|https_proxy|all_proxy|no_proxy|HTTP_PROXY|HTTPS_PROXY|ALL_PROXY|NO_PROXY)='
```

判定标准：
- 进程环境里能看到代理变量
- Gateway 日志中的重试风暴显著下降
- 消息通道恢复稳定

