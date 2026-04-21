# Autorunne 自动识别 / 自动初始化 / 自动恢复（0.6.3）

## 目标
让用户尽量不写提示词、不重复解释项目，而是：
- 打开仓库
- Autorunne 自动判断当前项目状态
- 自动创建或恢复 `.autorunne/`
- 让主流 coding agent 直接进入工作状态

## 现在的落地方式
### 1. `autorunne open`
`autorunne open` 依然是进入仓库的核心入口；0.6.3 这次把“状态层”进一步补成了更完整的工作流 CLI：旧 workspace 可迁移、status 读 state、task 可显式操作、恢复提示会自动忽略 `.vscode/` 这类噪音。

它会自动判断：
- 当前是不是 Git 仓库
- `.autorunne/` 是否已经存在
- 项目大概处于 greenfield / active / established 哪个阶段
- 最近有没有脏文件、最近改动集中在哪
- 当前更适合从哪里恢复

### 2. 如果是半成品项目但还没有 `.autorunne/`
`autorunne open` 会自动：
- 扫描项目技术栈
- 建立 `.autorunne/state/*`
- 渲染 `.autorunne/views/*`
- 自动生成 `AGENTS.md`
- 自动生成 `.agents/skills/autorunne-workflow/SKILL.md`
- 自动生成 `.claude/skills/autorunne-workflow/SKILL.md`
- 自动生成 `ar-codex / ar-claude / ar-hermes`
- 生成 `resume hint`

### 3. 如果项目已经有 `.autorunne/`
`autorunne open` 会自动：
- 刷新项目扫描结果
- 保留已有长期记忆
- 必要时把旧 markdown 工作流导入 state
- 更新 `.autorunne/views/START_HERE.md` / `.autorunne/views/COMMANDS.md`
- 在 `SESSION_LOG.md` 里追加一次 auto-resume 记录
- 更新下一步建议

## VS Code 自动进入工作状态
执行一次：

```bash
autorunne open --with-vscode
```

会生成 `.vscode/tasks.json`，让 VS Code 在 `folderOpen` 时自动执行：

```bash
autorunne open
```

这意味着：
- 第一次打开半成品项目：自动建 `.autorunne/`
- 之后再次打开：自动恢复工作状态

## Daemon 模式
如果你想让仓库在本地持续保持热状态，可以执行：

```bash
autorunne daemon --duration 300 --interval 2
```

它会先执行一次 `autorunne open`，然后在设定窗口内：
- 监听本地文件变化
- 检测到变化后自动 `sync`
- 把变化续写到现有 `.autorunne/` 工作流里

这适合：
- 本地持续开发
- 让仓库在一个工作时段里持续保持最新状态
- 后面再接更强的后台守护模式

## Hermes 聊天入口直写任务
如果你希望 Hermes 成为任务入口，现在可以直接走：

```bash
autorunne hermes-task \
  --task "继续支付回调" \
  --next "先补 webhook 合约测试" \
  --context "用户在 Hermes 里要求继续做支付回调"
```

它会自动：
- 先 `open` 当前仓库
- 必要时 bootstrap `.autorunne/`
- 把任务写进 state
- 把下一步写进 state 并渲染到 `NEXT_ACTION.md`
- 在 `SESSION_LOG.md` 里记录来源是 Hermes
- 可选把 durable decision 直接写进 `DECISIONS.md`

## 对 Hermes / Cursor / Copilot / Claude Code / Codex 的意义
Autorunne 不是去绑死某个模型，而是先把 repo 本地状态准备好。

所以真正的分工是：
- Autorunne：负责自动识别、项目记忆、恢复、交接
- Hermes / Cursor / Copilot / Claude Code / Codex：负责读这些文件并继续开发

## 当前阶段最重要的事
0.6.3 这一轮已经把“状态层 / 视图层 / skill 接入层 / wrapper 接入层 / legacy migration / 显式 task 操作”打通了。

这一版新增的关键补强是：
- `autorunne migrate`：把旧 markdown-only 工作区安全升级进 state
- `autorunne status`：直接看真实 state，不再只看临时扫描推断
- `autorunne task add/done/remove`：把 backlog / known unknowns / 完成项真正纳入 CLI
- 扫描器会自动降低 `.vscode/` 等编辑器噪音权重

下一步更适合继续加的是：
- JSON 输出模式，方便 wrapper / demo / agent 直接消费
- 更强的 release / changelog / publish 自动化
- 更深的 monorepo 图谱感知

## 后续可以继续加的方向
- 后台 daemon 模式常驻化
- 更强的增量变更摘要
- 按 agent 类型生成更细的入口文件
- 结合 Hermes 聊天入口自动把任务写进 `TASKS.md`
- 可选的大模型摘要增强层
