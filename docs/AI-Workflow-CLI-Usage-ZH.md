# AI Workflow CLI 使用说明（中文版）

## 1. 工具定位
AI Workflow CLI（命令名：`awf`）用于给任何 Git 项目挂上一层本地专用 AI 工作流，同时让正式发布版本保持干净。

它适合：
- 新项目
- 开发到一半的项目
- 从 GitHub 拉下来的开源项目
- 需要让 Claude Code、Codex、Hermes、Cursor 等模型快速进入开发状态的项目

## 2. 0.3.0 核心升级
- 新增 `awf release`，可生成正式发布包目录和发布说明
- 更强项目识别：支持 monorepo / pnpm workspace / Turborepo / Next.js / Go / Rust 等
- 强化 `awf doctor`，检查工作流文件、git exclude、hooks、VS Code、pre-commit、安装产物
- 新增 `awf completion`，支持 bash / zsh / fish
- `awf hooks --with-pre-commit` 支持团队式接入

## 3. 安装
### 开发安装
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 未来公开后推荐安装
```bash
pipx install ai-workflow-cli
```

### 从 release 安装
```bash
pip install ai_workflow_cli-0.3.0-py3-none-any.whl
```

## 4. 典型命令
### 新项目初始化
```bash
awf init
awf init --with-vscode
```

### 接管已有项目
```bash
awf adopt
awf adopt --with-vscode
```

### 刷新工作流状态
```bash
awf sync
awf sync --note "今天修完登录问题，下一步做订单页"
```

### 健康检查
```bash
awf doctor
```

### 导出正式版本
```bash
awf export
```

### 创建 0.3.0 发布包
```bash
awf release --version 0.3.0
```

### 安装 hooks 和 pre-commit
```bash
awf hooks --with-pre-commit
```

### 输出 shell completion
```bash
awf completion zsh
```

## 5. 生成目录
```text
.ai-workflow/
├── PROJECT_CONTEXT.md
├── TASKS.md
├── DECISIONS.md
├── SESSION_LOG.md
├── RULES.md
├── NEXT_ACTION.md
├── agents/
│   ├── common.md
│   ├── claude-code.md
│   ├── codex.md
│   ├── hermes.md
│   └── cursor.md
└── snapshots/
    └── latest.json
```

## 6. VS Code 自动接入
使用：
```bash
awf adopt --with-vscode
```
会自动生成：
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

并在打开工作区时自动触发 `awf sync`。

## 7. 正式版与开发版分离
本工具默认通过 `.git/info/exclude` 隔离 `.ai-workflow/`。
这意味着：
- 本地开发阶段持续使用 AI 工作流
- 上游仓库不会自动混入内部工作流文件
- `awf export` 和 `awf release` 的正式产物不包含 `.ai-workflow/`

## 8. 当前验证情况
本版本已验证：
- 通用空仓库初始化
- Node / React / Vite / Next.js / pnpm workspace / Turborepo 风格项目识别
- Python / FastAPI 项目识别
- Go 项目识别
- `sync`、`doctor`、`export`、`release`、`hooks`、`completion` 基础可用
- 本地 pytest 通过
- wheel 安装验证通过
- GitHub Actions Python 3.11 / 3.12 通过

## 9. 适用模型
当前设计为模型中立，适用于：
- Claude Code
- Codex
- Hermes
- Cursor Agent
- 其他能读取项目文档的编码模型

## 10. 下一步建议
下一步可继续扩展：
- PyPI 发布
- pipx 正式安装流
- 文件监听自动 sync
- 更深 monorepo 识别
- 更多编辑器入口层
