from __future__ import annotations

import re
from datetime import datetime, timezone
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file


_TASKS_FALLBACK = """# Tasks

## Completed / inferred

## In progress
- [ ] Validate local run and test commands

## Next up
- [ ] Confirm the next concrete step.

## Known unknowns
- [ ] Confirm deployment flow
- [ ] Confirm protected or high-risk modules before large edits
"""


def _read_current_next_action(path: Path) -> str:
    if not path.exists():
        return "Confirm the next concrete step."
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return "Confirm the next concrete step."


def _replace_tasks_section(content: str, heading: str, body_lines: list[str]) -> str:
    body = "\n".join(body_lines).strip()
    replacement = f"## {heading}\n{body}\n\n"
    pattern = rf"(?ms)^## {re.escape(heading)}\n.*?(?=^## |\Z)"
    if re.search(pattern, content):
        updated = re.sub(pattern, replacement, content, count=1)
    else:
        updated = content.rstrip() + "\n\n" + replacement
    return updated.rstrip() + "\n"


def _append_completed_task(content: str, summary: str) -> str:
    pattern = r"(?ms)^## Completed / inferred\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content)
    completed_line = f"- [x] {summary}"
    if match:
        existing_lines = [line.rstrip() for line in match.group(1).splitlines() if line.strip()]
    else:
        existing_lines = []
    if completed_line not in existing_lines:
        existing_lines.append(completed_line)
    if not existing_lines:
        existing_lines = [completed_line]
    return _replace_tasks_section(content, "Completed / inferred", existing_lines)


def _update_tasks(content: str, summary: str, next_action: str) -> str:
    updated = _append_completed_task(content, summary)
    return _replace_tasks_section(updated, "Next up", [f"- [ ] {next_action}"])


def run(target: Path, summary: str, next_action: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne finish must run inside an existing git repository")

    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")
    next_action_path = workflow_file(repo_root, "NEXT_ACTION.md")
    tasks_path = workflow_file(repo_root, "TASKS.md")

    clean_summary = summary.strip()
    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"
    resolved_next_action = next_action.strip() if next_action else _read_current_next_action(next_action_path)
    existing_tasks = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else _TASKS_FALLBACK

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry_lines = [
        f"\n## {timestamp} | finish summary",
        f"- Summary: {clean_summary}",
        f"- Next action: {resolved_next_action}",
    ]
    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(entry_lines) + "\n", encoding="utf-8")
    next_action_path.write_text(f"# Next Action\n\n{resolved_next_action}\n", encoding="utf-8")
    tasks_path.write_text(_update_tasks(existing_tasks, clean_summary, resolved_next_action), encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "summary": clean_summary,
        "next_action": resolved_next_action,
    }
