# AI Workflow CLI 使用说明（中文版）

## 1. 工具定位
AI Workflow CLI（命令名：`awf`）用于给任何 Git 项目挂上一层本地专用的 AI 开发工作流，同时保证正式发布版本保持干净。

它适合：
- 新项目
- 开发到一半的项目
- 从 GitHub 拉下来的开源项目
- 需要让 Claude Code、Codex、Hermes、Cursor 等模型快速进入开发状态的项目

## 2. 核心特点
- 自动生成 `.ai-workflow/` 工作流目录
- 自动生成项目上下文、任务、决策、会话日志、下一步动作等文档
- 默认写入 `.git/info/exclude`，避免污染上游仓库
- 支持导出不带 AI 工作流的正式版本
- 支持 git hooks，在 checkout / merge 后自动刷新工作流

## 3. 安装
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

安装后可直接使用：
```bash
awf --help
```

## 4. 典型命令
### 新项目初始化
```bash
awf init
```

### 接管已有项目
```bash
awf adopt
```

### 刷新工作流状态
```bash
awf sync
awf sync --note "今天修完登录问题，下一步做订单页"
```

### 查看当前状态
```bash
awf status
```

### 检查工作流是否健康
```bash
awf doctor
```

### 导出正式版本
```bash
awf export
```

### 安装自动同步 hooks
```bash
awf hooks
```

## 5. 生成后的目录
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

## 6. 推荐工作流
1. 进入项目先运行 `awf adopt` 或 `awf init`
2. 让 AI 先读 `.ai-workflow/` 里的共享文档
3. 干活前看 `NEXT_ACTION.md`
4. 每完成一个阶段执行 `awf sync --note "本次完成内容"`
5. 发布正式版本前执行 `awf export`

## 7. 正式版本与开发版本分离
本工具默认通过 `.git/info/exclude` 隔离 `.ai-workflow/`。
这意味着：
- 本地开发阶段可以持续使用 AI 工作流
- GitHub 正式仓库不会自动带上这套内部工作流
- `awf export` 导出的版本不包含 `.ai-workflow/`

## 8. 当前验证情况
本版本已验证：
- 通用空仓库初始化
- Node / React / Vite 风格项目接管
- Python / FastAPI 风格项目接管
- sync、doctor、export、hooks 命令基础可用
- 本地 pytest 测试通过
- GitHub Actions 已配置 Python 3.11 / 3.12 CI

## 9. 适用模型
当前设计为模型中立，适用于：
- Claude Code
- Codex
- Hermes
- Cursor Agent
- 其他能读取项目文档的编码模型

## 10. 后续建议
下一步可继续扩展：
- VS Code 插件
- 文件监听自动 sync
- 版本发布命令 `awf release`
- 更强的项目结构识别能力
