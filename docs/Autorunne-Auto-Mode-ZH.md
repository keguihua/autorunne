# Autorunne 自动识别 / 自动初始化 / 自动恢复（0.5.0）

## 目标
让用户尽量不写提示词、不重复解释项目，而是：
- 打开仓库
- Autorunne 自动判断当前项目状态
- 自动创建或恢复 `.autorunne/`
- 让主流 coding agent 直接进入工作状态

## 现在的落地方式
### 1. `autorunne open`
这是 0.5.0 的核心入口。

它会自动判断：
- 当前是不是 Git 仓库
- `.autorunne/` 是否已经存在
- 项目大概处于 greenfield / active / established 哪个阶段
- 最近有没有脏文件、最近改动集中在哪

### 2. 如果是半成品项目但还没有 `.autorunne/`
`autorunne open` 会自动：
- 扫描项目技术栈
- 生成 `.autorunne/PROJECT_CONTEXT.md`
- 生成 `.autorunne/TASKS.md`
- 生成 `.autorunne/DECISIONS.md`
- 生成 `.autorunne/NEXT_ACTION.md`
- 生成 `.autorunne/START_HERE.md`
- 生成 `resume hint`

### 3. 如果项目已经有 `.autorunne/`
`autorunne open` 会自动：
- 刷新项目扫描结果
- 保留已有长期记忆
- 更新 `START_HERE.md` / `COMMANDS.md`
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

## 对 Hermes / Cursor / Copilot / Claude Code / Codex 的意义
Autorunne 不是去绑死某个模型，而是先把 repo 本地状态准备好。

所以真正的分工是：
- Autorunne：负责自动识别、项目记忆、恢复、交接
- Hermes / Cursor / Copilot / Claude Code / Codex：负责读这些文件并继续开发

## 当前还没有做的事
0.5.0 先做的是“本地运行时自动准备状态”。

还没有把“真正调用远程大模型写项目摘要”强绑定进 CLI，原因是：
- 不想把产品先做重
- 不想把基础工作流绑死在单一模型 API 上
- 先保证没有大模型也能完成自动识别 / 自动初始化 / 自动恢复

## 后续可以继续加的方向
- 后台 daemon 模式
- 更强的增量变更摘要
- 按 agent 类型生成更细的入口文件
- 结合 Hermes 聊天入口自动把任务写进 `TASKS.md`
- 可选的大模型摘要增强层
