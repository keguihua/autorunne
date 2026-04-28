# Autorunne 产品说明书

## 一句话定义
Autorunne 是一个 **本地优先的 AI 项目记忆与开发工作流层**，把任意 Git 仓库变成可持续推进、可恢复上下文、可多模型共享的开发工作区。

## 核心价值
- 让 Claude Code、Codex、Hermes、Cursor、Copilot 等代理共享同一套 repo-local 项目记忆
- 把开发过程中的上下文、任务、决策、下一步动作落到 `.autorunne/`
- 保持正式发布版本干净，不把内部工作流文件混进交付物
- 让“今天做一半、明天继续、换模型继续、换人继续”真正可行
- 0.6.13 起能稳定识别 frontend/backend/contracts 这类多包 Node/TypeScript 项目，不再因为根目录缺少 package.json 而回退 generic
- 0.6.14/0.6.16 起补齐轻量 Python 教学项目识别，并让 Codex、Claude、Hermes、Cursor、Copilot 的 repo 入口都自动回到同一套 Autorunne 工作流

## 适用对象
- 独立开发者
- AI 编程工作流重度用户
- 同时使用多个 coding agent 的团队
- 需要接手老项目 / 半成品项目的人
- 需要把开发态和交付态严格分开的服务商

## 产品结构
### 1. CLI 命令
- `autorunne init`
- `autorunne adopt`
- `autorunne open`
- `autorunne migrate`
- `autorunne start`
- `autorunne checkpoint`
- `autorunne finish`
- `autorunne record`
- `autorunne task add / done / remove`
- `autorunne status`
- `autorunne show / history / trace / render`
- `autorunne doctor`
- `autorunne export`
- `autorunne release`
- `autorunne hooks`
- `autorunne vscode`
- `autorunne completion`

### 2. 项目本地目录
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
└── snapshots/
```

### 3. 多模型共享层
- Hermes：聊天入口 / 执行入口
- Claude Code：高质量工程实现
- Codex：快速编码与验证
- Cursor：编辑器入口

## 典型工作流
1. 在项目里运行 `autorunne open --with-vscode`（新仓库也可以 `autorunne init`）
2. 如果仓库里已有旧 `.autorunne/*.md`，先执行 `autorunne migrate`
3. 让任意 coding agent 先读取 `.autorunne/views/START_HERE.md`
4. 开发过程中持续执行 `autorunne start / checkpoint / finish / record`
5. 需要显式维护 backlog 时使用 `autorunne task add / done / remove`
6. 需要正式交付时执行 `autorunne export` 或 `autorunne release`

## 当前版本定位：0.6.16
当前版本已经属于 **可在真实项目里持续使用、对外演示、早期商业交付验证的 Beta 产品**：
- 已有 state-first CLI 主路径
- 已支持 legacy markdown workspace 迁移
- 已支持显式 task 操作与状态观测命令
- 已支持 direct agent 模式：用户直接在 Hermes / Codex / Claude Code / Cursor 里发任务，Autorunne 在后台维护项目状态
- 已支持常见 frontend/backend/contracts 多包项目识别、命令派生和视图渲染
- 已支持轻量 Python 教学/demo 项目识别：`python app.py`、`python -m pytest -q` 可自动写入 handoff 文档
- 已能通过 GitHub Release 与 PyPI 发布，可用 `pipx install/upgrade autorunne` 安装升级
- 0.6.16 已完成 GitHub Release、PyPI、Hermes 服务器 venv、真实课程开发项目 smoke test 四层验证

## 商业稳定性结论
0.6.16 可以作为早期商业演示和教学/交付工作流的稳定版本使用，适合用来证明：
- 用户只给 agent 分配任务，不需要每次提醒“先读 Autorunne”；
- repo-local 项目记忆能跨 Codex / Claude Code / Hermes / Cursor / Copilot 复用；
- GitHub Release + PyPI 安装链路已经跑通；
- 真实课程开发 demo 已验证 open/sync/start/test/finish 闭环。

对外表述应保持克制：它是可商用验证的 Beta 工作流层，不要包装成“完全自动替代开发者”的企业成熟平台。

## 当前边界
还未完成：
- JSON 输出模式与更深的脚本化接入
- 更强的 release / changelog / publish 自动化
- 更复杂 monorepo 的依赖图谱和跨包任务关系
- 更细的商业版功能分层

## 推荐使用场景
- 先在自己的真实项目中连续使用 1~2 周
- 再把沉淀下来的最佳实践做成对外版本
