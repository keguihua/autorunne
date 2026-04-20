# Autorunne 使用说明（中文版）

## 1. 工具定位
Autorunne（命令名：`autorunne`）用于给任何 Git 项目挂上一层本地专用 AI 工作流，同时让正式发布版本保持干净。

它适合：
- 新项目
- 开发到一半的项目
- 从 GitHub 拉下来的开源项目
- 需要让 Claude Code、Codex、Hermes、Cursor 等模型快速进入开发状态的项目

## 2. 0.4.0 核心升级
- 新增 `autorunne watch`，开发时本地轮询文件变化并自动 sync
- 新增 C / C++ 识别（含 CMake 项目）
- 强化 Rust / Python / Node / monorepo / pnpm workspace / Turborepo 识别
- `autorunne release` 现在会生成 `MANIFEST.json`
- 为后续对外公开展示补齐产品化文案和结构

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
### 开发安装
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### 从 release 安装
```bash
pip install autorunne-0.4.0-py3-none-any.whl
```

### 未来公开后推荐安装
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
autorunne adopt
autorunne adopt --with-vscode
```

### 刷新工作流状态
```bash
autorunne sync
autorunne sync --note "今天修完登录问题，下一步做订单页"
```

### 收尾一个开发切片
```bash
autorunne finish --summary "修完登录问题" --next "开始做订单页筛选"
```

### 监听开发过程中的文件变化
```bash
autorunne watch --duration 60 --interval 1
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
autorunne release --version 0.4.0
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

## 7. VS Code 自动接入
使用：
```bash
autorunne adopt --with-vscode
```
会自动生成：
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

并在打开工作区时自动触发 `autorunne sync`。

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
- Hermes
- Cursor Agent
- 其他能读取项目文档的编码模型

## 11. 下一步建议
下一步可继续扩展：
- PyPI 发布
- pipx 正式安装流
- 更智能 watcher / 后台守护
- 更深 monorepo 感知
- 更多编辑器入口层
