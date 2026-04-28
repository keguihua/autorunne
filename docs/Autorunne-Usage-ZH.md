# Autorunne 使用说明（中文版）

## 1. 工具定位
Autorunne（命令名：`autorunne`）用于给任何 Git 项目挂上一层本地专用 AI 工作流，同时让正式发布版本保持干净。

它适合：
- 新项目
- 开发到一半的项目
- 从 GitHub 拉下来的开源项目
- 需要让 Claude Code、Codex、Hermes、Cursor、Copilot、Gemini 等模型快速进入开发状态的项目

## 2. 0.6.14 核心升级
- 0.6.14 补强了轻量 Python 教学 / demo 项目识别：即使没有 `pyproject.toml` 和 `requirements.txt`，只要有 `app.py`、`main.py`、`tests/` 等线索，也能识别为 Python 项目
- `COMMANDS.md` 会自动给出 `python app.py` 和 `python -m pytest -q`，不再让 agent 猜命令
- repo skill / AGENTS / Cursor / Copilot 指令会要求模型自动读取 Autorunne workflow，不需要用户每次提醒“先读 Autorunne”
- 0.6.13 修复了真实开发中常见的多包项目识别问题：根目录没有 `package.json`，但 `frontend/`、`backend/`、`contracts/` 等子目录有 `package.json` 时，不再误判为 `generic`
- `autorunne sync` 会把子项目提升为顶层项目摘要，例如 `multi-package Node/TypeScript`、`Vite frontend`、`Node.js backend`、`Hardhat smart contracts`
- `COMMANDS.md` 会从各子项目 scripts 自动派生命令，并加上 `cd 子目录 && ...` 前缀
- direct agent 模式仍然是默认产品形态：用户直接打开 Codex / Claude Code / Hermes 发任务即可
- `autorunne ingest` 让 agent 把新的自然语言任务写进 `.autorunne/`，不用再假装用户在跟 Autorunne 单独聊天
- `.autorunne/state/*` 继续作为唯一事实源，`.autorunne/views/*` 是给人和 agent 看的稳定入口

## 3. 当前支持的语言 / 项目类型
### Web / 应用 / 服务
- npm / pnpm / yarn / bun
- React
- Next.js
- Vite
- Vue
- Nuxt
- Svelte / SvelteKit
- Express
- NestJS
- monorepo / pnpm workspace / Turborepo / Nx 信号
- 根目录无 package.json、但存在 frontend/backend/contracts/apps/packages 子项目的多包 Node/TypeScript 项目

### Python
- pip
- poetry
- uv
- FastAPI
- Django
- Flask
- Streamlit
- 纯标准库 Python 教学 / demo 项目（例如 `app.py` + `tests/`）
- `http.server` / `ThreadingHTTPServer` 小型服务

### 系统 / 编译型语言
- Go
- Rust
- C
- C++
- CMake 风格 C/C++ 项目

## 4. 安装
### 推荐公开安装方式
```bash
pipx install autorunne
```

### 一键安装脚本（适合你在 VS Code 终端里直接输入一行命令）
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```

### 用公开 release wheel 固定安装一个版本
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh \
  | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.15 bash
```

安装完成后，直接进入你的仓库运行：
```bash
autorunne open --with-vscode
```

以后你再打开这个项目时，VS Code 会自动触发 Autorunne 进入工作状态。你也可以在普通终端里手动执行 `autorunne open`。

### 轻量 Python 项目使用方式（0.6.14）
如果项目没有 `pyproject.toml`、没有 `requirements.txt`，但有：

```text
app.py
tests/
README.md
```

直接运行：

```bash
autorunne sync
```

AutoRunne 会在 `.autorunne/views/COMMANDS.md` 里生成：

```bash
python app.py
python -m pytest -q
```

这样课程 demo、小型教学项目、标准库 HTTP server 项目也能直接作为 repo-local 交接本使用。

### 多包项目 / Monorepo 使用方式（0.6.13）
如果项目根目录没有 `package.json`，但有这些文件：

```text
frontend/package.json
backend/package.json
contracts/package.json
```

直接在项目根目录运行：

```bash
autorunne sync
```

AutoRunne 会自动识别：
- `frontend`：Vite / TypeScript 前端
- `backend`：Node.js 后端
- `contracts`：Hardhat 合约项目

并在 `.autorunne/views/COMMANDS.md` 里生成类似命令：

```text
frontend:build -> cd frontend && npm run build
backend:test -> cd backend && npm test
contracts:compile -> cd contracts && npm run compile
contracts:test -> cd contracts && npm test
```

也就是说，agent 不需要猜命令，打开 `START_HERE.md` / `COMMANDS.md` 就能接着做。

最实用的理解方式是：**Autorunne 是先装一次、每个仓库初始化一次，不是每次开发都要单独再开一个 Autorunne 窗口。**

- 第一次接管某个仓库：运行一次 `autorunne open --with-vscode`
- 后面正常打开 VS Code：自动触发 Autorunne
- 然后你直接在这个仓库终端里启动 Codex / Claude Code 就行
- 如果你走 `ar-codex / ar-claude / ar-hermes`，wrapper 现在会自动拉起 daemon；只有想单独保温仓库时，才额外运行 `autorunne daemon`

### 开发安装
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 从 release 安装
```bash
pip install autorunne-0.6.15-py3-none-any.whl
```

### 公开发布后的推荐安装
```bash
pipx install autorunne
```

## 5. 典型命令
### 新项目初始化
```bash
autorunne init
autorunne init --with-vscode
```

### 接管已有项目
```bash
autorunne open
autorunne open --with-vscode
```

第一次进入老项目时，Autorunne 会自动创建 `.autorunne/`；后续再次进入时，会自动恢复已有工作流状态，并自动安装 repo 级 skill 与 wrapper。

### 本地常驻自动续做
```bash
autorunne daemon --duration 300 --interval 2
autorunne daemon --duration 300 --interval 2 --max-syncs 1
```

- `--max-syncs 1` 适合“等第一次检测到有效改动并自动记录后就退出”这种场景
- daemon 现在会显示本次自动记录到底改动了哪些文件

### 从 agent 直接聊天入口写任务
```bash
autorunne ingest \
  --source codex \
  --task "继续支付回调" \
  --next "先补 webhook 合约测试" \
  --context "用户直接打开 Codex 后要求继续做支付回调"
```

如果任务明确来自 Hermes 聊天桥，旧别名依然可用：

```bash
autorunne hermes-task \
  --task "继续支付回调" \
  --next "先补 webhook 合约测试" \
  --context "用户在 Hermes 里要求继续做支付回调"
```

### 开始一个任务
```bash
autorunne start --task "实现支付回调" --next "先补 webhook 合约测试"
```

### 中途打一个检查点
```bash
autorunne checkpoint --summary "已理清 webhook payload" --next "开始接 handler wiring"
```

### 刷新工作流状态
```bash
autorunne sync
autorunne sync --note "今天修完登录问题，下一步做订单页"
```

### 收尾一个开发切片
```bash
autorunne finish --summary "修完登录问题" --task "检查登录逻辑" --next "开始做订单页筛选" --decision "登录态改成共用中间件"
```

### 强制指定验证命令
```bash
autorunne finish --summary "确认测试通过" --validate "pytest -q" --next "补发布说明"
```

### 监听开发过程中的文件变化
```bash
autorunne watch --duration 60 --interval 1
```

### 额外新增的状态观测 / 迁移 / 任务命令
```bash
autorunne migrate
autorunne status
autorunne record --summary "补一条项目级说明" --next "继续梳理 trace 文档"
autorunne render
autorunne show --section current
autorunne history --limit 5
autorunne trace --limit 10
autorunne task add --text "确认发布清单" --section next-up
autorunne task done --match "确认发布清单"
```

### 健康检查
```bash
autorunne doctor
```

### 导出正式版本
```bash
autorunne export
```

### 创建正式发布包目录
```bash
autorunne release --version 0.6.15
```

### 安装 hooks 和 pre-commit
```bash
autorunne hooks --with-pre-commit
```

### 输出 shell completion
```bash
autorunne completion zsh
```

## 6. 生成目录
```text
.autorunne/
├── state/
│   ├── current.json
│   ├── events.jsonl
│   ├── tasks.json
│   ├── decisions.json
│   └── sessions.json
├── views/
│   ├── PROJECT_CONTEXT.md
│   ├── TASKS.md
│   ├── DECISIONS.md
│   ├── SESSION_LOG.md
│   ├── RULES.md
│   ├── NEXT_ACTION.md
│   ├── COMMANDS.md
│   └── START_HERE.md
├── bin/
│   ├── ar-codex
│   ├── ar-claude
│   └── ar-hermes
├── agents/
│   ├── common.md
│   ├── claude-code.md
│   ├── codex.md
│   ├── hermes.md
│   ├── cursor.md
│   └── copilot.md
└── snapshots/
    └── latest.json

AGENTS.md
.agents/skills/autorunne-workflow/SKILL.md
.claude/skills/autorunne-workflow/SKILL.md
```

## 7. VS Code 自动接入
使用：
```bash
autorunne open --with-vscode
```
会自动生成：
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

并在打开工作区时自动触发 `autorunne open`。

## 8. 正式版与开发版分离
本工具默认通过 `.git/info/exclude` 隔离 `.autorunne/`。
这意味着：
- 本地开发阶段持续使用 AI 工作流
- 上游仓库不会自动混入内部工作流文件
- `autorunne export` 和 `autorunne release` 的正式产物不包含 `.autorunne/`

## 9. 当前验证情况
本版本已验证：
- 通用空仓库初始化
- Node / React / Vite / Next.js / pnpm workspace / Turborepo 风格项目识别
- Python / FastAPI 项目识别
- Go / Rust 项目识别
- C / C++ / CMake 项目识别
- `sync`、`watch`、`doctor`、`export`、`release`、`hooks`、`completion` 基础可用
- 本地 pytest 通过
- wheel 安装验证通过
- GitHub Actions Python 3.11 / 3.12 通过

## 10. 适用模型
当前设计为模型中立，适用于：
- Claude Code
- Codex
- Gemini
- Hermes
- Cursor Agent
- GitHub Copilot / Copilot Chat
- 其他能读取项目文档的编码模型

## 11. 下一步建议
下一步可继续扩展：
- PyPI 发布
- pipx 正式安装流
- 更智能 watcher / 后台守护
- 更深 monorepo 感知
- 更多编辑器入口层
