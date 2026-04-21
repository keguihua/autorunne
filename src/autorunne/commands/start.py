from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autorunne.commands.finish import _ensure_next_action, _normalize_task_text, _replace_tasks_section, _section_lines
from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file

_TASKS_FALLBACK = """# Tasks

## Completed / inferred

## In progress

## Next up
- [ ] Confirm the next concrete step.

## Known unknowns
- [ ] Confirm deployment flow
- [ ] Confirm protected or high-risk modules before large edits
"""


def _ensure_in_progress_task(content: str, task: str) -> str:
    existing = _section_lines(content, "In progress")
    open_line = f"- [ ] {task}"
    if not any(_normalize_task_text(line).lower() == task.lower() for line in existing):
        existing = [open_line, *existing]
    return _replace_tasks_section(content, "In progress", existing)


def run(target: Path, task: str, next_action: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne start must run inside an existing git repository")

    clean_task = task.strip()
    resolved_next_action = next_action.strip() if next_action else clean_task
    tasks_path = workflow_file(repo_root, "TASKS.md")
    next_action_path = workflow_file(repo_root, "NEXT_ACTION.md")
    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")

    existing_tasks = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else _TASKS_FALLBACK
    updated_tasks = _ensure_in_progress_task(existing_tasks, clean_task)
    updated_tasks = _ensure_next_action(updated_tasks, resolved_next_action)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"
    log_lines = [
        f"\n## {timestamp} | start task",
        f"- Task: {clean_task}",
        f"- Next action: {resolved_next_action}",
    ]

    tasks_path.write_text(updated_tasks, encoding="utf-8")
    next_action_path.write_text(f"# Next Action\n\n{resolved_next_action}\n", encoding="utf-8")
    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "task": clean_task,
        "next_action": resolved_next_action,
    }
