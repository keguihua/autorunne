# Autorunne 商业稳定性说明（0.6.16）

## 结论

Autorunne 0.6.16 当前可以作为 **早期商业演示、AI 编程课程、顾问交付流程标准化** 的稳定 Beta 版本使用。更准确地说，它是一个可商用验证的 Beta 工作流层。

它已经不是只停留在本地 demo 的脚本：

- GitHub Release 已发布：<https://github.com/keguihua/autorunne/releases/tag/v0.6.16>
- PyPI 已发布：`autorunne==0.6.16`
- 可用 `pipx install autorunne` 或 `pipx upgrade autorunne` 安装升级
- Hermes 服务器运行环境已确认是 `AutoRunne 0.6.16`
- 真实课程开发项目已跑通 `open → sync → start → test → finish`

## 适合现在对外承诺什么

可以承诺：

1. **repo-local 项目记忆**
   - 项目上下文、任务、决策、下一步、会话记录落在 `.autorunne/`。

2. **多 agent 接力**
   - Codex、Claude Code、Hermes、Cursor、GitHub Copilot 的 repo 入口都会指向同一套 Autorunne workflow。

3. **真实项目恢复**
   - 重新打开项目后，agent 可以先读 `.autorunne/views/START_HERE.md` 和 repo skill，接着上次状态继续。

4. **安装链路清楚**
   - 主路径是 PyPI / pipx；GitHub release wheel 是备用路径。

5. **轻量项目和多包项目演示可用**
   - 轻量 Python demo 可以识别 `python app.py`、`python -m pytest -q`。
   - frontend/backend/contracts 这类多包 Node/TypeScript 项目可以派生命令。

## 暂时不要过度承诺什么

不要把 0.6.16 说成：

- 已经是成熟企业版平台；
- 可以完全替代研发管理；
- 所有语言、所有 monorepo、所有 CI/CD 场景都已深度覆盖；
- 不需要人工验证就能自动发布业务系统。

更准确的说法是：

> Autorunne 是一个本地优先、轻量、可恢复、可多 agent 接力的 AI 开发工作流层；0.6.16 已经适合进入教学、交付和早期商业验证。

## 推荐成交场景

### 1. AI 编程课程
把 Autorunne 作为“项目持续推进方法论”的底层工具，让学员看到：

- 不是只问 AI 一次；
- 而是把项目状态持续写回 repo；
- 下节课、下个模型、下个 agent 都能继续。

### 2. 小型外包/交付项目
用于客户项目内部推进：

- 每次任务有开始、检查点、完成总结；
- 交付前可以导出/整理正式版本；
- 内部 AI 工作流状态和客户交付代码分开。

### 3. AI 开发顾问服务
作为顾问给客户搭建 AI coding workflow 的标准件：

- 安装一次；
- 每个 repo `autorunne open --with-vscode`；
- 后续直接在 Codex / Claude / Hermes / Cursor / Copilot 里派任务。

## 0.6.16 验证摘要

已验证：

```text
GitHub Release: v0.6.16
PyPI: autorunne==0.6.16
Runtime: AutoRunne 0.6.16
Course demo: 4 passed, finish validation passed
Repo integrations: claude, codex, copilot, cursor, hermes
Missing files: none
```

## 对外一句话

> Autorunne 0.6.16 已经可以作为“AI 项目持续开发工作流层”对外演示和早期成交：用户只管给 agent 分配任务，Autorunne 在 repo 里保存项目记忆、任务状态和下一步。
