# Autorunne 0.6.14 发布说明

0.6.14 是一个小而关键的收尾版本，主要补两件事：

1. 轻量 Python 教学 / demo 项目不再被误判为 `generic`。
2. 生成的 repo skill 和 agent 指令更明确：模型应该自动读取 Autorunne workflow，不需要用户每次提醒“先读 Autorunne”。

## 适合的项目

例如这种课程 demo：

```text
app.py
store.py
tests/test_store.py
README.md
```

即使没有 `pyproject.toml`、没有 `requirements.txt`，AutoRunne 也会识别为 Python 项目，并在 `.autorunne/views/COMMANDS.md` 生成：

```bash
python app.py
python -m pytest -q
```

如果代码中有 `http.server` 或 `ThreadingHTTPServer`，会记录为：

```text
Framework: python standard library, http.server
```

## 模型接手流程

`autorunne open` / `autorunne sync` 生成的本地指令会强调：

- agent 应自动加载 `.agents/skills/autorunne-workflow/SKILL.md` 或 `.claude/skills/autorunne-workflow/SKILL.md`
- agent 应先读 `.autorunne/views/START_HERE.md`
- 用户只需要直接给任务，不需要每次补一句“先读 Autorunne”

这保持了 AutoRunne 的产品边界：它不是新的聊天入口，而是 repo-local 项目记忆和交接层。

## 验证

- `python -m pytest tests/test_scanner.py tests/test_integrations.py -q`
- `python -m pytest -q`
- 在 `course-leads-demo` 中真实运行 `autorunne open`、`autorunne sync`、`python -m pytest -q`

## 推荐升级

```bash
pipx upgrade autorunne --pip-args '--no-cache-dir -i https://pypi.org/simple'
autorunne version
```

期望输出：

```text
AutoRunne 0.6.14
```
