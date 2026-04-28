# Autorunne 对外定位与销售话术

## 对外定位
Autorunne 是一个 **本地优先、轻量但可持续交接的 AI 项目记忆与开发工作流内核**。

它不是单纯聊天，不是重型 AI IDE，也不是一堆华而不实的自动化。

它真正解决的是：

> 当你已经在用 Claude Code、Codex、Gemini、Hermes、Cursor、GitHub Copilot 这类 coding agent 开发时，怎样让项目状态、任务推进、决策记录和收尾动作持续接得上。

## 核心卖点
### 1. 不怕断档
今天做到一半，明天继续；
Claude 做一半，Codex 接着做；
一个窗口关掉，另一个窗口打开，项目状态仍然在仓库里。

### 2. 不绑死单一工具
Autorunne 不依赖某个单一编辑器或单一模型，项目记忆就在本地仓库里。

### 3. 真正是“状态工作流”，不是散装提示词
现在 `.autorunne/state/*` 是唯一事实源，`status/show/history/trace` 能直接读状态，`migrate` 能接住旧项目，`task add/done/remove` 能显式维护 backlog。

### 4. start → checkpoint → finish 闭环清楚
不是只会“写代码”，而是把：
- 任务开始
- 中途进展
- 最终收尾
- 下一步
- 验证结果

都落到本地工作流里。

### 5. 开发态和交付态分离
内部 AI 工作流文件不会直接污染正式交付版本。

### 6. 0.6.13 更适合真实全栈项目
现在 frontend/backend/contracts 这类多包项目不会再因为根目录没有 `package.json` 被误判成 generic。Autorunne 会自动识别 Vite 前端、Node 后端、Hardhat 合约，并把可执行命令写进 `COMMANDS.md`。

### 7. 真正适合接项目
对外包、定制开发、AI 协作开发都更实用，因为它强调的是“把项目持续做完”。

## 一句话介绍模板
### 短版
Autorunne 是一个让 Claude Code、Codex、Hermes、Cursor、Copilot 等 coding agent 持续接力做项目的 repo-local 工作流内核。

### 中版
Autorunne 把任意 Git 仓库变成 AI-ready 的持续开发工作区，让多个 coding agent 共享项目记忆、任务状态、检查点和收尾流程，真正能接力把项目做完。

### 成交版
如果你已经在用 AI 写代码，你很快会发现：模型会写，但项目不会自己连续推进。Autorunne 解决的就是这个问题——它把项目上下文、任务、决策、检查点、收尾动作沉淀到本地工作区，让 Claude Code、Codex、Gemini 这类工具都能基于同一套项目状态继续干活，而不是每次重新开始。

## 适合谁
- 独立开发者
- 接项目的人
- 有多个 AI 编程工具的人
- 想把 AI 编码流程标准化的人
- 想做 AI 开发交付服务的人

## 不适合谁
- 只想偶尔问几句代码问题的人
- 想找一个全自动取代开发流程的平台的人
- 不关心项目交接、恢复、收尾的人

## 销售话术示例
### 话术 1
你不是缺一个更会聊天的 AI，你缺的是一个能让多个 coding agent 真正接力做项目的工作流内核。

### 话术 2
Autorunne 的价值不在“写第一段代码”，而在“让项目第 20 次、第 50 次迭代还能接得上”。

### 话术 3
Claude Code、Codex、Hermes、Cursor 很适合做实现，但真正把它们串起来、让项目不断档的，是 Autorunne 这层 repo-local 项目记忆。

### 话术 4
如果你已经在用 AI 开发，Autorunne 不是替代你现有工具，而是把你现有工具变得更能交接、更能恢复、更能持续推进。

## 对外避免的说法
- 避免说成“聊天机器人”
- 避免说成“全自动 AI IDE”
- 避免过度强调抽象 AI 概念
- 避免只说成 VS Code 插件
- 避免只说成 prompt 模板

## 推荐对外表述
- 本地优先 AI 开发工作流内核
- 多模型共享项目记忆层
- 适合真实开发交付的 AI 工作区
- 面向 Claude Code / Codex / Hermes / Cursor / Copilot 的 repo-local workflow layer
