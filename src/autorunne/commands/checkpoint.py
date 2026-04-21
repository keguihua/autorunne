from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autorunne.commands.finish import _ensure_next_action
from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file


def run(target: Path, summary: str, next_action: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne checkpoint must run inside an existing git repository")

    clean_summary = summary.strip()
    next_action_path = workflow_file(repo_root, "NEXT_ACTION.md")
    tasks_path = workflow_file(repo_root, "TASKS.md")
    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")

    resolved_next_action = next_action.strip() if next_action else clean_summary
    existing_tasks = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else "# Tasks\n"
    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"

    updated_tasks = _ensure_next_action(existing_tasks, resolved_next_action)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    log_lines = [
        f"\n## {timestamp} | checkpoint",
        f"- Summary: {clean_summary}",
        f"- Next action: {resolved_next_action}",
    ]

    tasks_path.write_text(updated_tasks, encoding="utf-8")
    next_action_path.write_text(f"# Next Action\n\n{resolved_next_action}\n", encoding="utf-8")
    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "summary": clean_summary,
        "next_action": resolved_next_action,
    }
