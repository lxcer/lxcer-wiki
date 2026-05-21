#!/usr/bin/env python3
"""Daily GitHub Hunter for lxcer-wiki.

Scans GitHub without cloning repositories, fetches README files, classifies projects,
and writes a standalone GitHub recommendations section into the wiki.

Design goals:
- ~5 repos/day
- blend fastest-rising (tracked star delta) + high-star recent activity
- no repo clone; only GitHub REST + README raw content
- idempotent daily page generation
- optional safe git sync: commit -> pull --rebase -> push
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import math
import os
import re
import subprocess
import sys
import textwrap
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
WIKI = REPO_ROOT / "wiki" if (REPO_ROOT / "wiki" / "index.md").exists() else REPO_ROOT
STATE_DIR = REPO_ROOT / ".github-hunter"
STATE_FILE = STATE_DIR / "state.json"
SECTION_DIR = WIKI / "raw" / "github-hunter"
DAILY_DIR = SECTION_DIR / "daily"
INDEX_FILE = WIKI / "index.md"
LOG_FILE = WIKI / "log.md"
SCHEMA_FILE = WIKI / "SCHEMA.md"
TODAY = dt.date.today().isoformat()
NOW_ISO = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
USER_AGENT = "Hermes-GitHub-Hunter/1.0"

CATEGORY_RULES = [
    ("AI Agent", ["agent", "multi-agent", "autonomous", "mcp", "tool use", "function calling", "workflow"]),
    ("LLM / Model", ["llm", "large language", "transformer", "inference", "fine-tuning", "rag", "embedding", "vllm", "llama"]),
    ("AI App / Product", ["chatbot", "copilot", "assistant", "ai app", "生成式", "prompt"]),
    ("Developer Tool", ["cli", "sdk", "framework", "debug", "testing", "devtool", "developer", "api", "typescript", "python"]),
    ("Data / Infra", ["database", "vector", "postgres", "kubernetes", "docker", "observability", "pipeline", "etl"]),
    ("Web / App", ["react", "next.js", "frontend", "app", "ui", "dashboard", "mobile"]),
]

SEARCH_QUERIES = [
    # New fast-growing candidates, weighted toward projects where daily discovery matters.
    {"name": "new-fast-rising", "q": "created:>={date7} stars:>20 archived:false fork:false", "sort": "stars", "order": "desc", "per_page": 15},
    # Recently active high-star repos.
    {"name": "active-high-star", "q": "pushed:>={date14} stars:>1000 archived:false fork:false", "sort": "stars", "order": "desc", "per_page": 15},
    # AI/agent focused, matching the wiki domain.
    {"name": "ai-agent-rising", "q": "({terms}) pushed:>={date30} stars:>50 archived:false fork:false", "sort": "stars", "order": "desc", "per_page": 15},
]
AI_TERMS = "ai OR llm OR agent OR mcp OR rag"


def load_env_token() -> str | None:
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if token:
        return token.strip()
    env_file = Path.home() / ".hermes" / ".env"
    try:
        for line in env_file.read_text(encoding="utf-8").splitlines():
            if line.startswith("GITHUB_TOKEN=") or line.startswith("GH_TOKEN="):
                return line.split("=", 1)[1].strip().strip('"').strip("'")
    except FileNotFoundError:
        pass
    return None


def github_get(url: str, token: str | None = None, accept: str = "application/vnd.github+json") -> Any:
    headers = {"User-Agent": USER_AGENT, "Accept": accept, "X-GitHub-Api-Version": "2022-11-28"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = resp.read()
            ctype = resp.headers.get("content-type", "")
            if "application/json" in ctype or accept.endswith("json"):
                return json.loads(data.decode("utf-8"))
            return data.decode("utf-8", errors="replace")
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:500]
        raise RuntimeError(f"GitHub HTTP {e.code} for {url}: {body}") from e


def search_repos(token: str | None) -> dict[str, dict[str, Any]]:
    date7 = (dt.date.today() - dt.timedelta(days=7)).isoformat()
    date14 = (dt.date.today() - dt.timedelta(days=14)).isoformat()
    date30 = (dt.date.today() - dt.timedelta(days=30)).isoformat()
    repos: dict[str, dict[str, Any]] = {}
    for cfg in SEARCH_QUERIES:
        q = cfg["q"].format(date7=date7, date14=date14, date30=date30, terms=AI_TERMS)
        params = urllib.parse.urlencode({"q": q, "sort": cfg["sort"], "order": cfg["order"], "per_page": cfg["per_page"]})
        url = f"https://api.github.com/search/repositories?{params}"
        try:
            data = github_get(url, token)
        except Exception as exc:  # keep other queries alive
            print(f"WARN search failed: {cfg['name']}: {exc}", file=sys.stderr)
            continue
        for item in data.get("items", []):
            full = item["full_name"]
            existing = repos.setdefault(full, item)
            sources = existing.setdefault("hunter_sources", [])
            sources.append(cfg["name"])
        time.sleep(1.1)  # unauthenticated search API is sensitive to bursts
    return repos


def load_state() -> dict[str, Any]:
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except Exception:
            return {"repos": {}}
    return {"repos": {}}


def save_state(state: dict[str, Any]) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")


def fetch_readme(repo: dict[str, Any], token: str | None) -> str:
    full = repo["full_name"]
    url = f"https://api.github.com/repos/{full}/readme"
    try:
        data = github_get(url, token)
        if isinstance(data, dict) and data.get("content"):
            raw = base64.b64decode(data["content"], validate=False)
            return raw.decode("utf-8", errors="replace")
    except Exception as exc:
        print(f"WARN readme API failed for {full}: {exc}", file=sys.stderr)
    # Fallback to raw URL against default branch.
    branch = repo.get("default_branch") or "main"
    for candidate in [branch, "main", "master"]:
        raw_url = f"https://raw.githubusercontent.com/{full}/{candidate}/README.md"
        try:
            return github_get(raw_url, token=None, accept="text/plain")
        except Exception:
            continue
    return ""


def clean_text(md: str, max_chars: int = 5000) -> str:
    md = re.sub(r"<!--.*?-->", "", md, flags=re.S)
    md = re.sub(r"```.*?```", "", md, flags=re.S)
    md = re.sub(r"!\[[^\]]*\]\([^)]*\)", "", md)
    md = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", md)
    md = re.sub(r"<[^>]+>", " ", md)
    md = re.sub(r"[ \t]+", " ", md)
    md = re.sub(r"\n{3,}", "\n\n", md).strip()
    return md[:max_chars]


def first_heading(md: str, fallback: str) -> str:
    for line in md.splitlines()[:40]:
        m = re.match(r"^#\s+(.+)", line.strip())
        if m:
            return re.sub(r"[#*_`\[\]()]", "", m.group(1)).strip()[:100]
    return fallback


def extract_candidate_paragraphs(md: str, limit: int = 4) -> list[str]:
    text = clean_text(md, 9000)
    paras = []
    for p in re.split(r"\n\s*\n", text):
        p = re.sub(r"\s+", " ", p).strip(" -•\t")
        if len(p) < 45 or len(p) > 800:
            continue
        if re.search(r"^(installation|install|usage|quick start|docs|license|table of contents|contributing|security)\b", p, re.I):
            continue
        if re.search(r"badge|shields.io|npm install|pip install", p, re.I):
            continue
        paras.append(p)
        if len(paras) >= limit:
            break
    return paras


def extract_bullets(md: str, limit: int = 5) -> list[str]:
    bullets: list[str] = []
    capture = False
    for line in clean_text(md, 10000).splitlines():
        s = line.strip()
        if re.match(r"^#{1,3}\s+(features|key features|what.*does|capabilities|why|overview|亮点|特性|功能|简介)", s, re.I):
            capture = True
            continue
        if capture and s.startswith("#"):
            break
        if re.match(r"^[-*+]\s+", s):
            item = re.sub(r"^[-*+]\s+", "", s).strip()
            if 10 <= len(item) <= 180 and not re.search(r"badge|license|npm install|pip install|sponsor", item, re.I):
                bullets.append(item)
                if len(bullets) >= limit:
                    break
    return bullets


def has_cjk(text: str) -> bool:
    return bool(re.search(r"[\u4e00-\u9fff]", text or ""))


def zh_phrase(text: str) -> str:
    """Lightweight terminology translation for README-derived snippets."""
    if not text:
        return ""
    replacements = [
        (r"personal AI assistant", "个人 AI 助手"),
        (r"AI assistant", "AI 助手"),
        (r"coding agents?", "编程 Agent"),
        (r"agent harness", "Agent 执行框架"),
        (r"command line", "命令行"),
        (r"CLI", "命令行工具"),
        (r"workflow", "工作流"),
        (r"workflows", "工作流"),
        (r"developer tools?", "开发者工具"),
        (r"framework", "框架"),
        (r"skills?", "技能"),
        (r"memory", "记忆"),
        (r"security", "安全"),
        (r"research", "研究"),
        (r"open-source", "开源"),
        (r"open source", "开源"),
        (r"local-first", "本地优先"),
        (r"automation", "自动化"),
        (r"platform", "平台"),
        (r"performance optimization", "性能优化"),
        (r"reusable", "可复用"),
        (r"methodology", "方法论"),
        (r"large language models?", "大语言模型"),
        (r"language models?", "语言模型"),
    ]
    out = text
    for pat, repl in replacements:
        out = re.sub(pat, repl, out, flags=re.I)
    out = re.sub(r"\[[^\]]*\]\([^)]*\)", "", out)
    out = re.sub(r"[`*_>#]+", "", out)
    out = re.sub(r"\s+", " ", out).strip()
    return out


def infer_use_cases(category: str, keywords: list[str]) -> str:
    hay = " ".join([category, *keywords]).lower()
    cases = []
    if "agent" in hay:
        cases.append("构建或增强 AI Agent / 编程 Agent 工作流")
    if "mcp" in hay:
        cases.append("接入 MCP 或工具调用生态")
    if "llm" in hay or "rag" in hay:
        cases.append("大模型应用、RAG 或推理链路实验")
    if "cli" in hay or "developer" in hay or "开发者" in hay:
        cases.append("开发者工具链、命令行自动化或工程效率提升")
    if "web" in hay or "app" in hay:
        cases.append("产品原型、Web/App 形态的 AI 助手或控制台")
    if not cases:
        cases.append("作为开源项目样本继续观察其定位、实现方式和社区反馈")
    return "；".join(cases[:3])


def make_chinese_intro(repo: dict[str, Any], md: str) -> str:
    """Create a Chinese-first project introduction from metadata + README.

    Avoids dumping raw README prose. Non-Chinese README descriptions are converted
    into a Chinese analytical introduction based on metadata, topics, category,
    language, and detected technical signals.
    """
    owner = repo["owner"]["login"] if isinstance(repo.get("owner"), dict) else repo["full_name"].split("/")[0]
    lang = repo.get("language") or "未标注语言"
    category = repo.get("hunter_category", "Other")
    topics = repo.get("topics") or []
    keywords = extract_keywords(repo, md)
    topic_text = "、".join(topics[:8]) if topics else "暂无官方 topics"
    use_cases = infer_use_cases(category, keywords)
    stars = int(repo.get("stargazers_count") or 0)
    delta = int(repo.get("star_delta") or 0)
    updated = (repo.get("pushed_at") or repo.get("updated_at") or "")[:10]

    keyword_hay = " ".join(keywords).lower()
    focus = []
    if "agent" in keyword_hay:
        focus.append("Agent 编排、工具调用或编程助手能力")
    if "mcp" in keyword_hay:
        focus.append("MCP/外部工具生态接入")
    if "llm" in keyword_hay or "rag" in keyword_hay:
        focus.append("大模型应用链路与知识检索能力")
    if "cli" in keyword_hay:
        focus.append("命令行使用体验与自动化入口")
    if "developer" in keyword_hay or "开发者" in keyword_hay:
        focus.append("开发者工作流和工程效率")
    if "web" in keyword_hay or "app" in keyword_hay:
        focus.append("Web/App 产品形态与用户交互")
    if not focus:
        focus.append("项目定位、实现方式和社区反馈")

    maturity = "热度很高" if stars >= 10000 else "具备一定关注度" if stars >= 1000 else "处于早期观察阶段"
    growth = "本次观测仍有增长" if delta > 0 else "本次观测暂未体现新增 star，后续需要结合连续多日数据判断趋势"

    return (
        f"这是由 {owner} 维护的 {category} 类开源项目，当前主要语言为 {lang}。"
        f"从仓库分类、topics 和 README 结构信号判断，它更适合被放入“{use_cases}”这一类观察池。"
        f"项目当前 star 约 {stars}，属于{maturity}项目；{growth}。"
        f"关键词显示它值得关注的方向包括：{'、'.join(focus[:5])}。"
        f"官方 topics 为：{topic_text}。"
        f"后续评估时建议重点看三件事：第一，README 是否提供清晰的安装、运行和示例；第二，提交与 issue 是否持续活跃；第三，它是否能转化为可复用的 AI 产品能力、开发者工具或工作流资产。"
    )

def extract_keywords(repo: dict[str, Any], md: str) -> list[str]:
    keywords: list[str] = []
    def add(x: str | None):
        if not x:
            return
        x = re.sub(r"[^A-Za-z0-9_+.#\-/\u4e00-\u9fff ]", "", str(x)).strip()
        if x and x.lower() not in {k.lower() for k in keywords}:
            keywords.append(x)
    add(repo.get("hunter_category"))
    add(repo.get("language"))
    for t in repo.get("topics") or []:
        add(t)
    hay = " ".join([repo.get("description") or "", clean_text(md, 2500)]).lower()
    vocab = [
        ("AI Agent", ["agent", "multi-agent", "autonomous"]),
        ("MCP", ["mcp", "model context protocol"]),
        ("LLM", ["llm", "large language model", "language model"]),
        ("RAG", ["rag", "retrieval"]),
        ("CLI", ["cli", "command line"]),
        ("开发者工具", ["developer", "devtool", "debug", "testing"]),
        ("本地优先", ["local-first", "local first"]),
        ("工作流", ["workflow", "automation"]),
        ("开源", ["open source", "open-source"]),
    ]
    for label, needles in vocab:
        if any(n in hay for n in needles):
            add(label)
    return keywords[:10]


def summarize_readme(repo: dict[str, Any], md: str) -> str:
    return make_chinese_intro(repo, md)

def classify(repo: dict[str, Any], md: str) -> str:
    hay = " ".join([
        str(repo.get("name") or ""),
        str(repo.get("description") or ""),
        str(repo.get("language") or ""),
        " ".join(str(t) for t in (repo.get("topics") or []) if t),
        clean_text(md, 2500),
    ]).lower()
    scores: list[tuple[int, str]] = []
    for category, keys in CATEGORY_RULES:
        score = sum(1 for k in keys if k.lower() in hay)
        scores.append((score, category))
    scores.sort(reverse=True)
    return scores[0][1] if scores and scores[0][0] > 0 else "Other"


def score_repo(repo: dict[str, Any], previous: dict[str, Any]) -> tuple[float, int]:
    stars = int(repo.get("stargazers_count") or 0)
    prev = previous.get(repo["full_name"], {})
    prev_stars = int(prev.get("stars") or stars)
    delta = max(0, stars - prev_stars)
    created = repo.get("created_at", "")[:10]
    age_days = 365
    try:
        age_days = max(1, (dt.date.today() - dt.date.fromisoformat(created)).days)
    except Exception:
        pass
    # New projects with many stars are treated as rising even before historical state exists.
    velocity_proxy = stars / max(age_days, 1)
    source_bonus = 25 if "new-fast-rising" in repo.get("hunter_sources", []) else 0
    ai_bonus = 18 if "ai-agent-rising" in repo.get("hunter_sources", []) else 0
    score = delta * 12 + velocity_proxy * 2 + math.log10(stars + 10) * 15 + source_bonus + ai_bonus
    return score, delta


def select_repos(candidates: dict[str, dict[str, Any]], state: dict[str, Any], limit: int) -> list[dict[str, Any]]:
    previous = state.get("repos", {})
    scored = []
    for repo in candidates.values():
        if repo.get("stargazers_count", 0) < 20:
            continue
        score, delta = score_repo(repo, previous)
        repo["hunter_score"] = round(score, 2)
        repo["star_delta"] = delta
        scored.append(repo)
    scored.sort(key=lambda r: (r["hunter_score"], r.get("stargazers_count", 0)), reverse=True)
    # Balance categories: take top items but avoid all coming from one category after README classification.
    return scored[: max(limit * 3, limit)]


def md_escape(text: str) -> str:
    return (text or "").replace("|", "\\|").replace("\n", " ").strip()


def write_outputs(repos: list[dict[str, Any]]) -> tuple[Path, Path]:
    SECTION_DIR.mkdir(parents=True, exist_ok=True)
    DAILY_DIR.mkdir(parents=True, exist_ok=True)
    daily = DAILY_DIR / f"{TODAY}.md"

    lines = [
        "---",
        f'title: "GitHub Hunter Daily - {TODAY}"',
        f"created: {TODAY}",
        f"updated: {TODAY}",
        "type: summary",
        "tags: [survey, open-source, tool-use]",
        "sources: []",
        "contradictions: []",
        "---",
        "",
        f"# GitHub Hunter Daily - {TODAY}",
        "",
        "> 自动扫描 GitHub 项目：综合 star 上升速度（有历史数据时）、近期新项目热度、高 star 且近期活跃项目；不 clone 仓库，只快速读取 README。",
        "",
        "## 今日推荐",
        "",
        "| 项目 | 分类 | Stars | 观测增长 | 作者 | 创建时间 | 最近更新 | 关键词 | 原始链接 |",
        "|---|---:|---:|---:|---|---|---|---|---|",
    ]
    for r in repos:
        owner = r["owner"]["login"] if isinstance(r.get("owner"), dict) else r["full_name"].split("/")[0]
        lines.append(
            "| "
            + " | ".join([
                f"**{md_escape(r['full_name'])}**",
                md_escape(r["hunter_category"]),
                str(r.get("stargazers_count", 0)),
                str(r.get("star_delta", 0)),
                md_escape(owner),
                md_escape((r.get("created_at") or "")[:10]),
                md_escape((r.get("pushed_at") or r.get("updated_at") or "")[:10]),
                md_escape("、".join(r.get("hunter_keywords", []))),
                f"[GitHub]({r['html_url']})",
            ])
            + " |"
        )
    lines += ["", "## 分项目速览", ""]
    for i, r in enumerate(repos, 1):
        owner = r["owner"]["login"] if isinstance(r.get("owner"), dict) else r["full_name"].split("/")[0]
        title = first_heading(r.get("readme", ""), r["name"])
        lines += [
            f"### {i}. {r['full_name']} — {title}",
            "",
            f"- 分类：{r['hunter_category']}",
            f"- 作者/组织：{owner}",
            f"- 时间：创建 {(r.get('created_at') or '')[:10]}；最近更新 {(r.get('pushed_at') or r.get('updated_at') or '')[:10]}",
            f"- Stars：{r.get('stargazers_count', 0)}；观测增长：{r.get('star_delta', 0)}；语言：{r.get('language') or 'N/A'}",
            f"- 原始链接：{r['html_url']}",
            f"- 关键词：{'、'.join(r.get('hunter_keywords', []))}",
            "",
            "#### 项目介绍",
            "",
            r["hunter_summary"],
        ]
        lines.append("")
    daily.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")

    # Hub page: keep a stable recommendation page and append latest archive link.
    hub = SECTION_DIR / "index.md"
    archive_rows = []
    if hub.exists():
        content = hub.read_text(encoding="utf-8")
        archive_rows = re.findall(r"\| \[\[daily/[^\n]+", content)
    archive_link = f"| [[raw/github-hunter/daily/{TODAY}]] | {TODAY} | {len(repos)} | " + ", ".join(sorted({r["hunter_category"] for r in repos})) + " |"
    # Rebuild archive from actual daily files for idempotency.
    rows = []
    for p in sorted(DAILY_DIR.glob("*.md"), reverse=True)[:60]:
        date = p.stem
        if date == TODAY:
            rows.append(archive_link)
        else:
            rows.append(f"| [[raw/github-hunter/daily/{date}]] | {date} | - | 历史记录 |")
    hub_lines = [
        "---",
        "title: \"GitHub Hunter 推荐页\"",
        f"created: {TODAY}",
        f"updated: {TODAY}",
        "type: summary",
        "tags: [survey, open-source, tool-use]",
        "sources: []",
        "contradictions: []",
        "---",
        "",
        "# GitHub Hunter 推荐页",
        "",
        "这个栏位用于每日自动收集 GitHub 值得关注的开源项目，重点关注：",
        "",
        "- star 上升较快的新项目；",
        "- star 较高且近期仍活跃的项目；",
        "- 与 AI 产品、Agent、LLM、开发者工具、数据/基础设施相关的项目。",
        "",
        f"## 最新推荐（{TODAY}）",
        "",
        "| 项目 | 分类 | Stars | 增长 | 关键词 | 项目介绍 | 链接 |",
        "|---|---:|---:|---:|---|---|---|",
    ]
    for r in repos:
        hub_lines.append(
            "| " + " | ".join([
                f"**{md_escape(r['full_name'])}**",
                md_escape(r["hunter_category"]),
                str(r.get("stargazers_count", 0)),
                str(r.get("star_delta", 0)),
                md_escape("、".join(r.get("hunter_keywords", []))),
                md_escape(r["hunter_summary"][:260]),
                f"[GitHub]({r['html_url']})",
            ]) + " |"
        )
    hub_lines += [
        "",
        "## 分类导航",
        "",
    ]
    by_cat: dict[str, list[dict[str, Any]]] = {}
    for r in repos:
        by_cat.setdefault(r["hunter_category"], []).append(r)
    for cat in sorted(by_cat):
        hub_lines.append(f"### {cat}")
        for r in by_cat[cat]:
            hub_lines.append(f"- [{r['full_name']}]({r['html_url']})：关键词：{'、'.join(r.get('hunter_keywords', []))}；介绍：{r['hunter_summary']}")
        hub_lines.append("")
    hub_lines += [
        "## 历史归档",
        "",
        "| 页面 | 日期 | 数量 | 分类 |",
        "|---|---:|---:|---|",
        *rows,
        "",
        "## 相关页面",
        "",
        "- [[index]]",
        "- [[log]]",
    ]
    hub.write_text("\n".join(hub_lines).rstrip() + "\n", encoding="utf-8")
    return hub, daily


def update_wiki_index() -> None:
    content = INDEX_FILE.read_text(encoding="utf-8")
    if "## GitHub Hunter 推荐" not in content:
        insert = """
---

## GitHub Hunter 推荐

每日自动扫描 GitHub 项目，按增长、热度和 README 快速理解整理，原始推荐页放在 raw/github-hunter。

| 页面 | 用途 | 摘要 |
|------|------|------|
| [[raw/github-hunter/index]] | 推荐页 | 每日 GitHub 开源项目推荐与分类导航 |
"""
        marker = "---\n\n## 元页面"
        if marker in content:
            content = content.replace(marker, insert + "\n" + marker, 1)
        else:
            content += insert
    # update modified/last updated conservatively
    content = re.sub(r"modified: \d{4}-\d{2}-\d{2}", f"modified: {TODAY}", content)
    content = re.sub(r"\*最后更新: \d{4}-\d{2}-\d{2}\*", f"*最后更新: {TODAY}*", content)
    if "- GitHub Hunter: 1" not in content:
        content = content.replace("- 综合分析: 0\n", "- 综合分析: 0\n- GitHub Hunter: 1\n")
    content = re.sub(r"- \*\*总计: \d+\*\*", "- **总计: 13**", content)
    INDEX_FILE.write_text(content, encoding="utf-8")


def update_log(repos: list[dict[str, Any]], hub: Path, daily: Path) -> None:
    content = LOG_FILE.read_text(encoding="utf-8")
    content = re.sub(r"modified: \d{4}-\d{2}-\d{2}", f"modified: {TODAY}", content)
    names = ", ".join(r["full_name"] for r in repos)
    entry = f"""
---

## [{TODAY}] ingest | GitHub Hunter 每日推荐

**来源**: GitHub Search API + README 快速抓取（不 clone 仓库）

**操作内容**:
1. 扫描 star 上升/新项目热度与高 star 活跃项目
2. 读取候选项目 README 并提取中文项目介绍、关键词、作者、时间、原始链接与分类
3. 更新独立栏位 `raw/github-hunter/`

**更新文件**:
- `{hub.relative_to(WIKI)}`
- `{daily.relative_to(WIKI)}`
- `index.md`
- `.github-hunter/state.json`

**今日项目**: {names}

---
"""
    # Idempotency: remove same day GitHub Hunter entry before append at top after first separator.
    content = re.sub(rf"\n---\n\n## \[{TODAY}\] ingest \| GitHub Hunter 每日推荐.*?(?=\n---\n\n## \[|\n---\n\n\*日志格式|\Z)", "", content, flags=re.S)
    marker = "---\n\n## ["
    if marker in content:
        content = content.replace(marker, entry + "\n## [", 1)
    else:
        content += entry
    LOG_FILE.write_text(content, encoding="utf-8")


def git_sync(files: list[Path]) -> None:
    rels: list[str] = []
    for p in files:
        pp = p if isinstance(p, Path) else Path(str(p))
        if pp.is_absolute():
            try:
                rels.append(str(pp.relative_to(WIKI)))
            except ValueError:
                # fallback for files maintained outside wiki/ (e.g. .github-hunter/state.json)
                rels.append(str(pp))
        else:
            rels.append(str(pp))
    # Include state for star-delta tracking; okay to version, no secrets.
    cmds = [
        ["git", "add", *rels],
        ["git", "commit", "-m", f"docs: update github hunter {TODAY}"],
        ["git", "pull", "--rebase", "origin", current_branch()],
        ["git", "push", "origin", current_branch()],
    ]
    for cmd in cmds:
        try:
            out = subprocess.run(cmd, cwd=WIKI, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=180)
        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f"git command timed out: {' '.join(cmd)}") from exc
        if out.returncode != 0:
            # No-op commit is acceptable.
            if cmd[:2] == ["git", "commit"] and "nothing to commit" in out.stdout:
                continue
            raise RuntimeError(f"git command failed ({' '.join(cmd)}):\n{out.stdout}")


def current_branch() -> str:
    out = subprocess.check_output(["git", "branch", "--show-current"], cwd=WIKI, text=True).strip()
    return out or "main"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=5, help="number of repos to publish")
    parser.add_argument("--sync-git", action="store_true", help="commit, pull --rebase, and push wiki updates")
    parser.add_argument("--dry-run", action="store_true", help="scan and print candidates without writing files")
    args = parser.parse_args()

    token = load_env_token()
    state = load_state()
    candidates = search_repos(token)
    if not candidates:
        raise RuntimeError("No GitHub candidates returned; check network or GitHub API rate limit.")
    selected_pool = select_repos(candidates, state, args.limit)

    enriched: list[dict[str, Any]] = []
    seen_categories: set[str] = set()
    for repo in selected_pool:
        if len(enriched) >= args.limit:
            break
        readme = fetch_readme(repo, token)
        repo["readme"] = readme[:12000]
        repo["hunter_category"] = classify(repo, readme)
        repo["hunter_summary"] = summarize_readme(repo, readme)
        repo["hunter_keywords"] = extract_keywords(repo, readme)
        # avoid filling all slots with the same class unless needed
        if len(enriched) < args.limit - 1 and repo["hunter_category"] in seen_categories and len(seen_categories) >= 3:
            pass
        enriched.append(repo)
        seen_categories.add(repo["hunter_category"])
        time.sleep(0.4)

    if len(enriched) < args.limit:
        for repo in selected_pool:
            if repo in enriched:
                continue
            readme = repo.get("readme") or fetch_readme(repo, token)
            repo["readme"] = readme[:12000]
            repo["hunter_category"] = classify(repo, readme)
            repo["hunter_summary"] = summarize_readme(repo, readme)
            repo["hunter_keywords"] = extract_keywords(repo, readme)
            enriched.append(repo)
            if len(enriched) >= args.limit:
                break

    # Update state after selection.
    state.setdefault("repos", {})
    for repo in candidates.values():
        state["repos"][repo["full_name"]] = {
            "stars": int(repo.get("stargazers_count") or 0),
            "last_seen": NOW_ISO,
            "html_url": repo.get("html_url"),
        }
    state["last_run"] = NOW_ISO

    if args.dry_run:
        print(json.dumps({"date": TODAY, "repos": [r["full_name"] for r in enriched]}, ensure_ascii=False, indent=2))
        return 0

    hub, daily = write_outputs(enriched)
    update_wiki_index()
    save_state(state)
    update_log(enriched, hub, daily)

    changed = [hub, daily, INDEX_FILE, LOG_FILE, STATE_FILE]
    if args.sync_git:
        git_sync(changed)

    result = {
        "status": "ok",
        "date": TODAY,
        "count": len(enriched),
        "hub": str(hub),
        "daily": str(daily),
        "repos": [
            {
                "full_name": r["full_name"],
                "category": r["hunter_category"],
                "stars": r.get("stargazers_count"),
                "star_delta": r.get("star_delta"),
                "url": r.get("html_url"),
            }
            for r in enriched
        ],
        "git_synced": bool(args.sync_git),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({"status": "error", "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        raise
