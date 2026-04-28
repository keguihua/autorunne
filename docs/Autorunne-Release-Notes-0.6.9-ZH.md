# Autorunne 0.6.9 发布说明

发布日期：2026-04-23

## 这版最重要的一句话

**用户现在应该直接打开 Codex / Hermes / Claude Code 发任务，Autorunne 只在背后维护项目状态和记忆。**

## 本次升级重点

### 1. direct agent 变成默认产品形态
现在生成出来的 repo 指令、`START_HERE.md`、AGENTS、Codex / Claude / Hermes skill 都统一改成：

- 用户直接打开 agent
- 直接说任务
- 不要求用户先“通过 Autorunne 聊天”
- Autorunne 只做后台 workflow / state / memory layer

### 2. 新增 `autorunne ingest`
新增了一个 agent-neutral 入口命令：

```bash
autorunne ingest --source codex --task "继续当前任务"
```

它的作用是：
- 把 direct Codex / Claude Code / Hermes 里的自然语言任务写进 `.autorunne/`
- 记录来源 agent
- 自动 bootstrapped / resumed workspace
- 启动任务状态，而不再把这个能力绑定在 `hermes-task` 这个名字上

### 3. `hermes-task` 保留兼容
老的：

```bash
autorunne hermes-task ...
```

仍然保留，适合 Hermes 聊天桥场景。

但从产品表达上，0.6.9 以后推荐优先讲：

- direct agent
- `autorunne ingest`
- Autorunne 在后台工作

### 4. wrappers 降级为“可选兜底入口”
`ar-codex / ar-claude / ar-hermes` 还在，仍然有用。

但现在文档和生成指令里都明确变成：

- **可选 fallback**
- 不是默认要求用户走的入口

也就是说，用户正常直接开 Codex / Claude Code / Hermes 就行；只有你特别想要“硬 Autorunne entrypoint”时，才用 wrapper。

## 典型新用法

### 用户视角
1. 进入 repo
2. 打开 Codex / Claude Code / Hermes
3. 直接发任务

### agent 背后做的事
1. 读取 `.autorunne/views/START_HERE.md`
2. 如有必要，用 `autorunne ingest --source <agent> --task ...` 记录新任务
3. 开发过程中继续走 checkpoint / finish / sync
4. 让 `.autorunne/` 保持最新

## 本次验证

### 自动化验证
已通过：

```bash
python -m pytest tests/test_cli.py tests/test_integrations.py -q
python -m pytest -q
```

### 真实 smoke
做了一个 direct-agent 风格最小验证：
- `autorunne open`
- `autorunne ingest --source codex ...`
- 写入最小文档改动
- `autorunne auto-finish --source codex`

确认：
- `TASKS.md` 从 in-progress 进入 completed
- `SESSION_LOG.md` 记录 `codex task ingress`
- `current.json` 回到 `active_task = null`

## 当前版本结论

**0.6.9 的产品表达已经明确切到：agent 在前，Autorunne 在后。**

这更接近真实用户体验：

> 打开项目，打开 Codex / Hermes / Claude Code，直接发任务就行。
> Autorunne 只会在背后自动维护项目状态和记忆。
