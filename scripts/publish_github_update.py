#!/usr/bin/env python3
"""Publish a version update post to GitHub Discussions.

Usage:
  python scripts/publish_github_update.py --version 0.6.20
  python scripts/publish_github_update.py --version 0.6.20 --dry-run

The script uses the GitHub CLI (`gh`) for authentication. It never stores tokens.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str], *, input_text: str | None = None) -> str:
    result = subprocess.run(
        cmd,
        input=input_text,
        text=True,
        cwd=ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip()
        raise SystemExit(f"Command failed: {' '.join(cmd)}\n{message}")
    return result.stdout.strip()


def detect_owner_repo() -> tuple[str, str]:
    url = run(["git", "remote", "get-url", "origin"])
    match = re.search(r"github\.com[:/]([^/]+)/([^/.]+)(?:\.git)?$", url)
    if not match:
        raise SystemExit(f"Cannot detect GitHub owner/repo from origin: {url}")
    return match.group(1), match.group(2)


def graphql(query: str, variables: dict) -> dict:
    args = ["gh", "api", "graphql", "-f", f"query={query}"]
    for key, value in variables.items():
        args.extend(["-F", f"{key}={value}"])
    return json.loads(run(args))


def repo_and_category(owner: str, repo: str, category: str) -> tuple[str, str]:
    query = """
    query($owner:String!, $repo:String!) {
      repository(owner:$owner, name:$repo) {
        id
        discussionCategories(first: 50) { nodes { id name slug } }
      }
    }
    """
    data = graphql(query, {"owner": owner, "repo": repo})["data"]["repository"]
    repo_id = data["id"]
    categories = data["discussionCategories"]["nodes"]
    wanted = category.lower()
    for item in categories:
        if item["name"].lower() == wanted or item["slug"].lower() == wanted:
            return repo_id, item["id"]
    available = ", ".join(item["name"] for item in categories) or "none"
    raise SystemExit(f"Discussion category not found: {category}. Available: {available}")


def existing_discussion(owner: str, repo: str, title: str) -> str | None:
    query = """
    query($owner:String!, $repo:String!) {
      repository(owner:$owner, name:$repo) {
        discussions(first: 50, orderBy: {field: CREATED_AT, direction: DESC}) {
          nodes { title url }
        }
      }
    }
    """
    nodes = graphql(query, {"owner": owner, "repo": repo})["data"]["repository"]["discussions"]["nodes"]
    for item in nodes:
        if item["title"].strip() == title.strip():
            return item["url"]
    return None


def changelog_section(version: str) -> str:
    path = ROOT / "CHANGELOG.md"
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    pattern = rf"(^##\s+{re.escape(version)}\b.*?)(?=^##\s+\d+\.\d+\.\d+\b|\Z)"
    match = re.search(pattern, text, flags=re.M | re.S)
    return match.group(1).strip() if match else ""


def default_body(version: str) -> str:
    section = changelog_section(version)
    release_url = f"https://github.com/HUAFIRE777/autorunne/releases/tag/v{version}"
    pypi_url = f"https://pypi.org/project/autorunne/{version}/"

    if version == "0.6.34":
        intro = """Autorunne 0.6.34 发布了。

这是一版专门为长期项目准备的状态可靠性补丁。你仍然只需要打开项目、直接给 AI 派任务；Autorunne 继续在仓库本地告诉下一个 Agent：项目做到哪里、正在做什么、验证过什么、下一步是什么。"""
        bullets = """
- 多线程、多进程同时写状态时统一串行化，不再互相覆盖
- JSON 原子保存，并保留最近一次有效备份
- 状态和备份都损坏时 fail closed，不会静默清空项目历史
- `events.jsonl` 只修复真正的末尾半行，完整坏记录不会被误删
- 长期记忆 compact 支持同月追加和崩溃幂等恢复
- pending compact 会在任何新状态写入前完成；恢复失败时阻止新写入，避免旧计划覆盖新进展
""".strip()
        why = """简单说：Autorunne 0.6.34 没有增加一堆新按钮，而是把“让 AI 长期记得项目做到哪里”这件事做得更稳。特别适合持续几个月、跨 Codex / Claude Code / Hermes / Cursor 反复接力的项目。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.31":
        intro = """Autorunne 0.6.31 发布了。

这版补上一次真实 dogfood 暴露的小断点：用户不应该为了 Autorunne 的 checkpoint / finish 自己写 summary。现在 agent 或旧 wrapper 直接调用也能自动生成进度说明。"""
        bullets = """
- `autorunne checkpoint` 可以省略 `--summary`，自动根据改动文件或当前任务生成进度说明
- `autorunne finish` 也可以省略 `--summary`，自动生成完成总结
- 显式传 `--summary` 时仍然优先使用，旧写法和新写法可以并行
- repo handoff 文案提醒 agent 自主记录，不要向用户索要 workflow summary
- 继续保留 0.6.30 的自动长期记忆压缩
""".strip()
        why = """简单说：用户只派任务，Autorunne 在后台自己记进度。即使老 agent 指令还在跑 `autorunne checkpoint`，也不会因为缺少 summary 打断自动化。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.30":
        intro = """Autorunne 0.6.30 发布了。

这版把 0.6.29 的长期项目记忆管理继续自动化：项目反复迭代时，Autorunne 会自动写入进展；记录超过默认阈值后，自动把旧历史压缩归档。"""
        bullets = """
- 默认超过 1000 条 session/event 后自动 compact
- 自动 compact 默认保留最近 200 条详细记录
- 更早历史归档到 `.autorunne/archive/YYYY-MM.md`，不是直接删除
- 新增配置：`auto_compact_enabled`、`auto_compact_threshold`、`auto_compact_keep_sessions`
- 已接入 open/sync/ingest/start/checkpoint/finish 等常用写入路径
""".strip()
        why = """简单说：用户不用每天盯 `.autorunne/` 有多少记录。Autorunne 平时持续记录项目进展，记录太多时自动收纳旧历史，handoff 入口继续保持短而清楚。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\n查看项目记忆体积：\n\n```bash\nautorunne memory-report\n```\n\n如需改成 500 条触发，可编辑 `.autorunne/config.json`：\n\n```json\n{{\n  \"auto_compact_threshold\": 500,\n  \"auto_compact_keep_sessions\": 200\n}}\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.29":
        intro = """Autorunne 0.6.29 发布了。

这版把 Autorunne 从“开发交接层”继续推进到“长期项目记忆层”：项目从创建、反复迭代、上线，到后期维护，`.autorunne/` 都可以一直伴随存在，但不会让日志无限膨胀。"""
        bullets = """
- 新增 `autorunne compact`：默认保留最近 200 条详细记录，更早历史归档到 `.autorunne/archive/`
- 新增 `autorunne compact --dry-run`：先预览会压缩什么，不直接改状态
- 新增 `autorunne memory-report`：查看 `.autorunne` 体积、sessions/events 数量和是否建议 compact
- 新增 `autorunne export-session`：把最近开发记录导出成可分享的 Markdown 报告
- compact 会生成 `.autorunne/SUMMARY.md`，沉淀长期项目摘要、关键决策和下一步
""".strip()
        why = """简单说：Autorunne 不保存完整聊天垃圾，而是保留近期上下文、归档长期历史，让下一个 agent 既能接上项目，又不会被旧日志淹没。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\n查看项目记忆体积：\n\n```bash\nautorunne memory-report\n```\n\n预览长期记忆压缩：\n\n```bash\nautorunne compact --dry-run\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.28":
        intro = """Autorunne 0.6.28 发布了。

这版是 0.6.27 核心 handoff 通过真实复测后的干净度补丁：不大改已通过的交接逻辑，只把 status / doctor / integration diff 的噪音降下来。"""
        bullets = """
- `autorunne status` 不再把 root START_HERE mirror 缺失误报成核心 Missing files
- 新增 `autorunne doctor --handoff`，只看交接一致性；handoff ok 就退出 0
- 默认 `autorunne doctor` 区分 Blocking issues 和 Optional warnings，hooks/pre-commit/wrappers/integrations 不再误阻断
- 继续保持 `.agents/.claude` 这类 workflow-only diff 与业务 changed_files 分离
""".strip()
        why = """简单说：下一个 agent 看到的会是真正阻断交接的问题，而不是可选安装项或 mirror 噪音。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\n只检查 handoff：\n\n```bash\nautorunne doctor --handoff\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.27":
        intro = """Autorunne 0.6.27 发布了。

这版是在 0.6.26 真实交接一致性修复上的继续加固：让多 agent 接手项目时更稳定、更干净、更不污染业务 diff。"""
        bullets = """
- `autorunne doctor` 新增 handoff 一致性检查，能指出具体漂移字段
- 新增 `autorunne repair-handoff`，可修复旧 workspace 里的下一步状态漂移
- workflow follow-up 不再进入主 `tasks.next_up[0]`，流程备注不会变成产品任务
- `finish` 会把 changed_files 分成 business / autorunne_state / integration，`.agents/.claude` 版本 diff 不再混入业务改动
""".strip()
        why = """简单说：项目交给下一个 agent 时，主下一步更可靠，业务改动也更干净。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n升级：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\n修复旧交接状态：\n\n```bash\nautorunne repair-handoff\nautorunne doctor\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.26":
        intro = """Autorunne 0.6.26 发布了。

这版修的是一次真实开发复测发现的交接一致性问题：任务完成、验证通过后，不同入口看到的“下一步”必须一致。"""
        bullets = """
- finish 后 current/tasks/NEXT_ACTION/START_HERE/status 会统一到同一个主下一步
- workflow_follow_up 只作为流程备注，不再覆盖主 next action
- current.json 新增结构化 last_validation，保留验证命令、状态、时间和输出摘要
- autorunne open 不再静默刷新已有 repo-local integration 文件版本，避免污染业务 diff
""".strip()
        why = """简单说：下一个 agent 打开项目时，不会再被旧 Lesson 或流程备注带偏。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.25":
        intro = """Autorunne 0.6.25 发布了。

这版是一个交接洁净度补丁：不改 0.6.24 已稳定的自动 Git 初始化，只让下一轮 AI/agent 打开项目时看到的状态更准确。"""
        bullets = """
- 已完成任务不会继续残留在 Next product task
- 发布基线、验证、状态刷新这类流程备注会归到 Workflow follow-up
- autorunne status 现在明确显示 Autorunne state tracked by git
- .autorunne/ 仍然默认是本地交接状态，不强制提交到 GitHub
""".strip()
        why = """简单说：下一轮 AI 接手项目时，更容易看清真正该做什么。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.24":
        intro = """Autorunne 0.6.24 发布了。

这版把新项目上手再简化一步：用户不需要先手动 `git init`，直接运行 `autorunne open` 就可以。"""
        bullets = """
- 新目录运行 autorunne open 会自动创建本地 Git 仓库
- autorunne init/adopt/ingest/hermes-task 也支持自动初始化 Git
- 已有 Git 仓库行为不变，继续保留原来的 repo-local 工作流
- 继续保留 0.6.22 的状态安全和 open 日志洁净度
""".strip()
        why = """简单说：新用户只需要打开项目，不需要先懂 Git 初始化这一步。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.23":
        intro = """Autorunne 0.6.23 发布了。

这版补了一个新手最容易忘的小提醒：新项目要先 `git init`，再运行 Autorunne。"""
        bullets = """
- 非 Git 目录运行 autorunne open/init 等命令时，会直接提醒先执行 git init
- CLI 会干净退出，不再给新手看一大段 traceback
- README 30 秒上手里也明确写了 git init → autorunne open
- 继续保留 0.6.22 的状态安全和 open 日志洁净度
""".strip()
        why = """简单说：第一次用 Autorunne 时更不容易卡住。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.22":
        intro = """Autorunne 0.6.22 发布了。

这版是在 0.6.21 核心状态修复通过真实项目验证后，继续打磨日志洁净度：重复打开工作区时，SESSION_LOG 更安静、更容易读。"""
        bullets = """
- 多次 autorunne open 触发的 workspace open auto-resume 会更稳地去重
- 即使中间夹着 integration refresh/noise，相同 auto-resume 也只更新时间，不继续刷屏
- start task / checkpoint / finish summary 仍会切开不同开发阶段，保留真正进展
- 0.6.21 的 finish next_product_task 安全修复继续保留
""".strip()
        why = """简单说：状态继续安全，日志更干净，下一轮 AI 打开项目时更容易接手。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.21":
        intro = """Autorunne 0.6.21 发布了。

这版只修一个很小但真实会误导下一轮 AI 的交接问题：finish 完成任务后，不再把刚完成的任务继续显示成 Next product task。"""
        bullets = """
- finish matched/active task 后，已完成任务不会再留在 next_product_task
- 如果还有 pending 产品任务，会自动回退到下一个产品任务
- 如果没有 pending 产品任务，状态视图会显示 Next product task：无
- workflow_follow_up 继续保留 finish --next 的流程跟进内容
""".strip()
        why = """简单说：下一轮 AI 打开项目时，不会再被“已经完成的任务”误导。"""
        return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()

    if version == "0.6.20":
        intro = """Autorunne 0.6.20 发布了。\n\n这版主要修的是我自己在真实项目交接里遇到的几个小痛点：状态看不清、日志太长、项目里的 agent skill 版本没有跟着 CLI 更新。"""
        bullets = """
- repo skill front matter 会跟着当前 CLI 版本更新，不再长期停在旧版本号
- STATUS.md 直接显示最后一次验证命令、结果和摘要
- SESSION_LOG 不再把完整 build/test 输出铺进去，只保留关键摘要
- workspace open / integration updated 这类重复记录更少，交接阅读更干净
""".strip()
        why = """简单说：下一轮 AI 打开项目时，更容易知道上次做了什么、测没测过、下一步该干什么。"""
    else:
        intro = f"Autorunne {version} 发布了。"
        bullets = section or "这次更新的详细内容请看 release notes。"
        why = ""

    return f"""{intro}\n\n{bullets}\n\n{why}\n\n安装或更新：\n\n```bash\npipx upgrade autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n新安装：\n\n```bash\npipx install autorunne --pip-args=\"--no-cache-dir -i https://pypi.org/simple\"\n```\n\n检查版本：\n\n```bash\nautorunne --version\n```\n\nRelease: {release_url}\nPyPI: {pypi_url}\n""".strip()


def create_discussion(repo_id: str, category_id: str, title: str, body: str) -> str:
    mutation = """
    mutation($repositoryId:ID!, $categoryId:ID!, $title:String!, $body:String!) {
      createDiscussion(input: {repositoryId:$repositoryId, categoryId:$categoryId, title:$title, body:$body}) {
        discussion { url }
      }
    }
    """
    data = graphql(
        mutation,
        {
            "repositoryId": repo_id,
            "categoryId": category_id,
            "title": title,
            "body": body,
        },
    )
    return data["data"]["createDiscussion"]["discussion"]["url"]


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish an Autorunne version update to GitHub Discussions.")
    parser.add_argument("--version", required=True, help="Version without leading v, e.g. 0.6.20")
    parser.add_argument("--title", help="Custom discussion title")
    parser.add_argument("--body-file", type=Path, help="Markdown body file. Defaults to a generated post.")
    parser.add_argument("--category", default="Announcements", help="Discussion category name or slug")
    parser.add_argument("--repo", help="GitHub repo in owner/name form. Defaults to git origin.")
    parser.add_argument("--dry-run", action="store_true", help="Print the post without publishing")
    args = parser.parse_args()

    if args.repo:
        owner, repo = args.repo.split("/", 1)
    else:
        owner, repo = detect_owner_repo()

    version = args.version.removeprefix("v")
    default_titles = {
        "0.6.34": "Autorunne 0.6.34 发布：长期项目状态更可靠",
        "0.6.31": "Autorunne 0.6.31 发布：summary 自动生成，不再让用户写流程说明",
        "0.6.30": "Autorunne 0.6.30 发布：自动长期记忆压缩",
        "0.6.29": "Autorunne 0.6.29 发布：长期项目记忆管理",
        "0.6.28": "Autorunne 0.6.28 发布：status / doctor 干净度补丁",
        "0.6.27": "Autorunne 0.6.27 发布：交接 doctor / repair 与 diff 分类加固",
        "0.6.26": "Autorunne 0.6.26 发布：真实交接状态一致性修复",
        "0.6.25": "Autorunne 0.6.25 发布：下一轮 AI 接手更干净",
        "0.6.24": "Autorunne 0.6.24 发布：新项目自动 Git 初始化",
        "0.6.23": "Autorunne 0.6.23 发布：新项目先 git init 的友好提醒",
        "0.6.22": "Autorunne 0.6.22 发布：workspace open 日志更干净",
        "0.6.21": "Autorunne 0.6.21 发布：完成任务后不再把它当下一步",
        "0.6.20": "Autorunne 0.6.20 发布：更干净的 AI 项目交接",
    }
    title = args.title or default_titles.get(version, f"Autorunne {version} 发布：版本更新")
    body = args.body_file.read_text(encoding="utf-8") if args.body_file else default_body(version)

    if args.dry_run:
        print(f"# {title}\n")
        print(body)
        return 0

    existing = existing_discussion(owner, repo, title)
    if existing:
        print(f"Discussion already exists: {existing}")
        return 0

    repo_id, category_id = repo_and_category(owner, repo, args.category)
    url = create_discussion(repo_id, category_id, title, body)
    print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
