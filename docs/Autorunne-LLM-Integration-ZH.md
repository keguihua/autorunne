# Autorunne 与大模型开发对接说明

## 1. Autorunne 的角色
Autorunne 不是新的大模型，也不是重型 AI IDE。

它做的是一层 **repo-local workflow layer（仓库本地工作流层）**：
- 把项目上下文写成本地文件
- 把任务推进状态写成本地文件
- 把阶段性决策写成本地文件
- 把每轮开发的开始、检查点、收尾写成本地文件

这样 Claude Code、Codex、Gemini、Hermes、Cursor、GitHub Copilot 这些窗口不需要“凭聊天记忆硬记住项目”，而是直接读取 `.autorunne/`。

## 2. 核心工作方式
当你在 VS Code 里打开一个项目后：

### 第一步：进入项目时自动接管
```bash
autorunne open --with-vscode
```

之后普通打开 VS Code 工作区时，Autorunne 就会自动进入工作状态，并自动准备这些文件：
- `PROJECT_CONTEXT.md`
- `TASKS.md`
- `DECISIONS.md`
- `SESSION_LOG.md`
- `NEXT_ACTION.md`
- `COMMANDS.md`
- `START_HERE.md`

### 第二步：把 `START_HERE.md` 给大模型窗口
无论你用的是：
- Claude Code
- Codex
- Gemini
- Hermes
- Cursor
- GitHub Copilot / Copilot Chat

都先让它读：
```text
.autorunne/START_HERE.md
```

这个文件会告诉模型：
- 先读哪些项目记忆文件
- 当前 next action 是什么
- 当前本地推荐跑什么命令
- 这个 repo 应该怎样继续开发

### 第三步：开始任务
```bash
autorunne start --task "实现支付回调" --next "先补 webhook 合约测试"
```

作用：
- 把任务写进 `TASKS.md` 的 `In progress`
- 把 next action 写进 `NEXT_ACTION.md`
- 在 `SESSION_LOG.md` 记录这轮工作开始了

### 第四步：开发中打检查点
```bash
autorunne checkpoint --summary "已理清 webhook payload" --next "开始接 handler wiring"
```

作用：
- 不结束任务
- 记录当前进展
- 更新下一步
- 方便换模型窗口、跨天续做、或给别人接手

### 第五步：完成一轮开发
```bash
autorunne finish \
  --summary "修完登录问题" \
  --task "检查登录逻辑" \
  --next "开始做订单页筛选" \
  --decision "登录态改成共用中间件"
```

作用：
- 关闭一个真实 task
- 更新 next action
- 记录 durable decision
- 记录这次动过哪些文件
- 把收尾写进 session log

## 3. 为什么这样更适合大模型开发
大模型最怕 4 件事：

### 1）只靠聊天上下文
聊天窗口一换、token 一压缩，就漂了。

### 2）项目状态不落地
模型知道“刚刚做了什么”，但 repo 里没有持久记录。

### 3）多个模型之间不能交接
Claude Code 看不见 Codex 的内部记忆，Gemini、Hermes、Cursor、GitHub Copilot 也看不见彼此窗口里的内部状态。

### 4）完成一轮开发后没有明确收尾动作
任务看似做完，实际上没人更新任务、下一步、决策、验证结果。

Autorunne 就是专门解决这 4 个问题。

## 4. 怎么让大模型实现“非常顺手的对接”
不是靠魔法，而是靠下面这套最稳的工作流：

### 规则 A：每次开新窗口先读 `.autorunne/`
永远先读：
1. `START_HERE.md`
2. `PROJECT_CONTEXT.md`
3. `TASKS.md`
4. `DECISIONS.md`
5. `NEXT_ACTION.md`
6. `COMMANDS.md`

### 规则 B：开始前用 `start`
让任务正式进入本地状态，而不是只存在聊天里。

### 规则 C：中间用 `checkpoint`
这样模型、你自己、甚至后续别的协作者都不会断片。

### 规则 D：结束时必须用 `finish`
这一步最重要。它负责把：
- 完成项
- 下一步
- 决策
- 文件变化
- 验证结果

都落回 repo。

### 规则 E：让模型把 `.autorunne/` 当作 source of truth
推荐直接给模型这段话：

```text
Use `.autorunne/` as the source of truth for this repo. Read START_HERE.md, PROJECT_CONTEXT.md, TASKS.md, DECISIONS.md, NEXT_ACTION.md, and COMMANDS.md before coding. Keep changes small, run the relevant local validation command, then update project memory with checkpoint or finish.
```

## 5. finish 的自动验证怎么工作
Autorunne 现在支持两种方式：

### 方式 A：自动验证
如果 repo 能探测到测试命令，`finish` 默认会自动跑它。
例如：
- Python 项目：`pytest`
- Node 项目：`npm test` / `pnpm test`
- Go：`go test ./...`
- Rust：`cargo test`

### 方式 B：手动指定验证命令
```bash
autorunne finish --summary "完成支付改造" --validate "pytest -q" --next "补发布说明"
```

如果验证失败，finish 会失败，不会假装已经完工。

## 6. 对外售卖时应该怎么讲
最适合的说法不是：
- “全自动 AI 编程平台”
- “替代工程师”
- “超级 IDE”

而是：

> Autorunne 是一个本地优先、轻量、可交接的 AI 开发工作流内核。它让 Claude Code、Codex、Gemini、Hermes、Cursor、GitHub Copilot 这类 coding agent 在同一个仓库里共享项目记忆、任务状态和收尾流程。

## 7. 一句话理解
### 大模型负责生成和执行
### Autorunne 负责记忆、交接、收尾、恢复

这就是它和普通聊天工具最大的区别。
