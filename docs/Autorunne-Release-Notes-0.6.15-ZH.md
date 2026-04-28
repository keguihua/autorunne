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
