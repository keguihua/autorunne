# Autorunne 0.6.15 发布说明

0.6.15 是 0.6.14 的小收尾补丁，重点不是新增项目识别，而是补齐“所有 agent 入口都应该自动回到 Autorunne workflow”。

## 这版修什么

0.6.14 已经让 Codex / Claude / Hermes 的 repo skill 写清楚：

- 自动加载 `.agents/skills/autorunne-workflow/SKILL.md` 或 `.claude/skills/autorunne-workflow/SKILL.md`
- 自动读取 `.autorunne/views/START_HERE.md`
- 不等用户每次提醒“先读 Autorunne”

0.6.15 继续把同样的规则写进：

- `.cursor/rules/autorunne-workflow.mdc`
- `.github/copilot-instructions.md`

这样 Cursor 和 GitHub Copilot 也会明确指向同一套 repo-local workflow。

## 用户应该怎么用

用户仍然只需要直接对自己正在用的 agent 发任务：

```text
帮我开发报名线索搜索功能
```

agent 侧应该自动：

1. 读取 repo skill / native rule
2. 读取 `.autorunne/views/START_HERE.md`
3. 如有新任务，用 `autorunne ingest --source <agent> --task <task>` 记录
4. 开发、测试、finish/checkpoint

## 推荐升级

```bash
pipx upgrade autorunne --pip-args '--no-cache-dir -i https://pypi.org/simple'
autorunne version
```

期望：

```text
AutoRunne 0.6.15
```


## 发布与验证状态

0.6.15 已完成四层验证：

1. GitHub Release：<https://github.com/keguihua/autorunne/releases/tag/v0.6.15>
2. PyPI：`autorunne==0.6.15`，包含 wheel 和 sdist
3. Hermes 服务器运行环境：`autorunne --version` 显示 `AutoRunne 0.6.15`
4. 真实课程开发项目 smoke test：

```bash
autorunne open --path .
autorunne sync --path .
autorunne start --path . --task "简单测试 Autorunne 0.6.15" --next "运行 pytest 并 finish"
python -m pytest -q
autorunne finish --path . --summary "Autorunne 0.6.15 简单验证通过" --validate "python -m pytest -q"
```

验证结果：

```text
4 passed
Validation: passed
Active task: none
Last action: task_finished
Missing files: none
```

## 商业稳定性判断

0.6.15 可以作为早期商业演示、AI 编程课程、顾问交付流程里的稳定 Beta 版本使用。

推荐对外说法：

> Autorunne 0.6.15 已跑通 GitHub Release、PyPI、真实服务器环境和课程开发项目 smoke test，适合用于演示“多 agent 共享 repo-local 项目记忆”的真实工作流。

同时保持边界清楚：它是轻量 workflow layer，不是最终企业级全自动研发平台。
