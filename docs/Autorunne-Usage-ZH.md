# Autorunne 使用说明（中文版）

## 1. 工具定位
Autorunne（命令名：`autorunne`）用于给任何 Git 项目挂上一层本地专用 AI 工作流，同时让正式发布版本保持干净。

它适合：
- 新项目
- 开发到一半的项目
- 从 GitHub 拉下来的开源项目
- 需要让 Claude Code、Codex、Hermes、Cursor、Copilot、Gemini 等模型快速进入开发状态的项目

## 2. 0.6.7 核心升级
- `.autorunne/state/*` 继续作为唯一事实源
- 新增 `autorunne migrate`，可以把旧的 markdown-only 工作区升级到 state workspace
- `status` 改成优先读取 state，能直接看到 active task / last action / task counts / integration 状态
- 新增显式任务操作：`autorunne task add`、`autorunne task done`、`autorunne task remove`
- `open / sync` 的恢复建议会自动降低 `.vscode/` 这类编辑器噪音权重
- `doctor` 会明确提示 legacy workspace 是否需要迁移

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

### Python
- pip
- poetry
- uv
- FastAPI
- Django
- Flask
- Streamlit

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
  | AUTORUNNE_INSTALL_SOURCE=release-wheel AUTORUNNE_VERSION=v0.6.7 bash
```

安装完成后，直接进入你的仓库运行：
```bash
autorunne open --with-vscode
```

以后你再打开这个项目时，VS Code 会自动触发 Autorunne 进入工作状态。你也可以在普通终端里手动执行 `autorunne open`。

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
pip install autorunne-0.6.7-py3-none-any.whl
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

### 从 Hermes 聊天入口直接写任务
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
autorunne release --version 0.6.7
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
