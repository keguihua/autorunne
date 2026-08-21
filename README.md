# Autorunne

[![CI](https://github.com/HUAFIRE777/autorunne/actions/workflows/ci.yml/badge.svg)](https://github.com/HUAFIRE777/autorunne/actions/workflows/ci.yml)
[![Release Packages](https://github.com/HUAFIRE777/autorunne/actions/workflows/release.yml/badge.svg)](https://github.com/HUAFIRE777/autorunne/actions/workflows/release.yml)

**Autorunne 是一个 repo-local 项目记忆和交接层：让 Codex、Claude Code、Hermes、Cursor、GitHub Copilot 在同一个 Git 仓库里接着做，而不是每次从零解释。**

很多人已经在用 AI 写代码，但真实项目最麻烦的不是“让模型写一段代码”，而是：今天做到一半，明天还能不能接上；换一个模型，能不能知道上次做了什么；交付前，能不能看清任务、决策、验证结果和下一步。

Autorunne 解决的是这个问题。

它会在项目里维护一个 `.autorunne/` 工作区，把项目上下文、任务、决策、会话记录、推荐命令、验证证据和下一步整理成稳定文件。你仍然用自己熟悉的工具写代码，Autorunne 只负责把项目状态留在仓库本地。

## 0.6.34 候选（release candidate）

0.6.34 保持现有 UX：AI 进入项目后仍然先看当前进度、任务和下一步。这一版只加强本地状态层：

- 并发状态写入串行化
- JSON 原子保存和最近一次有效备份
- 主文件与备份都坏时 fail closed，不静默清空
- `events.jsonl` 安全追加和尾部恢复
- 同月归档追加，压缩批次可幂等重试
- 版本元数据统一为 0.6.34

详细说明见 [0.6.34 状态可靠性候选说明](docs/Autorunne-Release-Notes-0.6.34-ZH.md)。在外部发布完成前，不要把候选版当成已经上线的 GitHub Release 或 PyPI 包。

继续保留 0.6.32 的缓存过滤、0.6.31 的零提示 `checkpoint` / `finish` 能力，以及长期记忆压缩功能。

## 适合谁

- 经常用 Codex、Claude Code、Hermes、Cursor 或 Copilot 做开发的人
- 独立开发者、接项目的人、AI 编程课程讲师
- 手里有半成品项目、老项目、客户项目，需要让 AI 快速接手的人
- 不想被某一个编辑器、某一个模型绑死的小团队

## 它不是什么

- 不是新的聊天机器人
- 不是重型 AI IDE
- 不是“完全替代开发者”的自动化平台
- 不是一套散装 prompt 模板

它更像一个放在仓库里的项目工作台：谁来干活都先看同一份项目状态。

## 安装

推荐用 `pipx`：

```bash
pipx install autorunne
```

如果你在 VS Code 终端里想一行装好：

```bash
curl -fsSL https://raw.githubusercontent.com/HUAFIRE777/autorunne/main/scripts/install.sh | bash
```

当前候选版本：**0.6.34**（release candidate；GitHub Release / PyPI 尚未发布）

## 发布 GitHub 版本说说

每次发新版后，可以用脚本自动发一条 GitHub Discussions 更新：

```bash
python scripts/publish_github_update.py --version 0.6.31
```

先预览、不发布：

```bash
python scripts/publish_github_update.py --version 0.6.31 --dry-run
```

脚本使用本机 `gh` 登录态，不保存 token。

## 30 秒上手

进入你的项目目录。新项目不需要手动 `git init`，Autorunne 会自动初始化本地 Git 仓库：

```bash
autorunne open --with-vscode
```

`autorunne open` 会创建或刷新 `.autorunne/`，并生成给不同 agent 看的入口文件。

之后日常使用很简单：

1. 打开项目
2. 启动 Codex / Claude Code / Hermes / Cursor / Copilot
3. 直接分配任务
4. agent 先读 `.autorunne/views/START_HERE.md`
5. 完成后用 Autorunne 记录验证结果和下一步

常用收尾命令：

```bash
autorunne finish --validate "python -m pytest -q" --next "继续做订单筛选"
```

## 仓库里会多出什么

```text
.autorunne/
├── state/                 # 机器可读的项目状态
├── views/                 # 给人和 agent 看的 Markdown
│   ├── START_HERE.md      # 新窗口从这里开始
│   ├── PROJECT_CONTEXT.md # 项目背景
│   ├── TASKS.md           # 任务状态
│   ├── DECISIONS.md       # 已确认的决策
│   ├── COMMANDS.md        # 推荐运行命令
│   └── STATUS.md          # 当前是否可继续开发
├── SUMMARY.md             # compact 生成的长期项目摘要
├── archive/               # compact 归档的旧 session/event 月度摘要
├── exports/               # export-session 生成的交付/复盘报告
└── bin/                   # 可选 wrapper，如 ar-codex / ar-claude / ar-hermes
```

这些文件默认服务于本地开发和团队交接。你可以按项目需要决定哪些文件提交到 GitHub，哪些只留在本机。

## 支持的入口

Autorunne 不是替代这些工具，而是让它们共享同一个仓库状态：

- Codex
- Claude Code
- Hermes
- Cursor
- GitHub Copilot
- Gemini

如果你想强制从 Autorunne wrapper 进入，也可以用：

```bash
./.autorunne/bin/ar-codex
./.autorunne/bin/ar-claude
./.autorunne/bin/ar-hermes
```

但正常情况下，直接打开你常用的 agent 发任务就行。

## 支持的项目类型

目前已经覆盖常见开发项目：

- Node / TypeScript：npm、pnpm、yarn、bun、React、Next.js、Vite、Vue、Nuxt、Svelte
- 多包项目：`frontend/`、`backend/`、`contracts/`、`apps/*`、`packages/*`
- Python：pip、poetry、uv、FastAPI、Django、Flask、Streamlit
- 轻量 Python 教学项目：只有 `app.py`、`main.py`、`tests/` 也能识别
- Go、Rust、C、C++、CMake 项目

## 常用命令

```bash
# 第一次接管或恢复项目
autorunne open --with-vscode

# 刷新项目扫描和视图
autorunne sync

# 记录一个来自 agent 的自然语言任务
autorunne ingest --source codex --task "继续支付回调" --next "先补 webhook 测试"

# 开始 / 检查点 / 完成
autorunne start --task "实现支付回调" --next "先写测试"
autorunne checkpoint --next "接 handler"   # summary 可省略，Autorunne 会自动生成
autorunne finish --validate "pytest -q" --next "补发布说明"

# 查看当前状态
autorunne status
autorunne doctor

# 长期项目记忆管理
autorunne memory-report
autorunne compact --dry-run
autorunne export-session --last 20
```

## 文档

建议按下面顺序看：

1. [GitHub 开源使用手册](docs/Autorunne-GitHub-开源使用手册-ZH.md)
2. [安装与使用操作手册](docs/Autorunne-操作手册-ZH.md)
3. [中文使用说明](docs/Autorunne-Usage-ZH.md)
4. [产品说明书](docs/Autorunne-产品说明书-ZH.md)
5. [开源宣传手册](docs/Autorunne-开源宣传手册-ZH.md)
6. [商业计划书](docs/Autorunne-商业计划书-ZH.md)
7. [对外定位与销售话术](docs/Autorunne-对外定位与销售话术-ZH.md)
8. [商业稳定性说明](docs/Autorunne-商业稳定性说明-ZH.md)
9. [0.6.20 PyPI/GitHub 同步发布说明](docs/Autorunne-Release-Notes-0.6.20-ZH.md)
10. [0.6.34 状态可靠性候选说明](docs/Autorunne-Release-Notes-0.6.34-ZH.md)
10. [0.6.31 自动 summary fallback](docs/Autorunne-Release-Notes-0.6.31-ZH.md)
10. [0.6.30 自动长期记忆压缩](docs/Autorunne-Release-Notes-0.6.30-ZH.md)
11. [0.6.29 长期项目记忆管理](docs/Autorunne-Release-Notes-0.6.29-ZH.md)
11. [0.6.28 status / doctor 干净度补丁](docs/Autorunne-Release-Notes-0.6.28-ZH.md)
11. [0.6.27 交接 doctor / repair 与 diff 分类加固](docs/Autorunne-Release-Notes-0.6.27-ZH.md)
11. [0.6.26 真实交接状态一致性补丁](docs/Autorunne-Release-Notes-0.6.26-ZH.md)
11. [0.6.25 交接洁净度补丁](docs/Autorunne-Release-Notes-0.6.25-ZH.md)
12. [0.6.24 自动 Git 初始化](docs/Autorunne-Release-Notes-0.6.24-ZH.md)
13. [0.6.23 git init 新手提醒](docs/Autorunne-Release-Notes-0.6.23-ZH.md)
14. [0.6.22 workspace open 日志洁净度打磨](docs/Autorunne-Release-Notes-0.6.22-ZH.md)
15. [0.6.21 finish next_product_task 回退修复](docs/Autorunne-Release-Notes-0.6.21-ZH.md)
12. [0.6.16 状态可视化发布说明](docs/Autorunne-Release-Notes-0.6.16-ZH.md)
12. [与大模型开发对接说明](docs/Autorunne-LLM-Integration-ZH.md)
13. [English usage guide](docs/Autorunne-Usage-EN.md)

## 当前阶段

0.6.34 候选版在不改变交接体验的前提下，把并发写入、损坏恢复和同月归档做成可验证的可靠性补丁。0.6.31 仍然让自动化更顺手：用户只派任务，agent / wrapper 可以直接调用 checkpoint 或 finish，Autorunne 自动生成 summary，不再因为缺少流程说明打断。

更准确地说：Autorunne 现在是一个可持续使用的 Beta 项目记忆层。它不是最终企业平台，但已经足够支撑真实项目里的“接着做”和上线后的日常维护。

## 开发安装

```bash
git clone https://github.com/HUAFIRE777/autorunne.git
cd autorunne
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m pytest -q
```

## License

MIT
