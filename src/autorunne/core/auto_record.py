from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import load_config
from autorunne.core.state_engine import collect_git_details, load_workspace_state, record_checkpoint, start_task, workflow_exists


def _compact_file_summary(changed_files: list[str], limit: int = 3) -> str:
    if not changed_files:
        return "the latest local changes"
    head = changed_files[:limit]
    summary = ", ".join(head)
    remaining = len(changed_files) - len(head)
    if remaining > 0:
        summary += f" (+{remaining} more)"
    return summary


def auto_record_local_change(repo_root: Path, *, changed_files: list[str], source: str) -> dict[str, object]:
    if not changed_files or not workflow_exists(repo_root):
        return {"auto_recorded": False, "auto_started": False, "summary": None, "task": None}

    config = load_config(repo_root)
    if not config.auto_record_on_change:
        return {"auto_recorded": False, "auto_started": False, "summary": None, "task": None}

    state = load_workspace_state(repo_root)
    current = state["current"]
    active_task = (current.get("active_task") or "").strip()
    file_summary = _compact_file_summary(changed_files)
    next_action = (current.get("next_action") or f"Review and continue the latest local changes in {file_summary}.").strip()

    auto_started = False
    task = active_task or None
    if not active_task:
        task = f"Review and continue the latest local changes in {file_summary}"
        start_task(repo_root, task, next_action)
        auto_started = True

    summary = f"Auto-recorded local changes via {source}: {_compact_file_summary(changed_files, limit=5)}"
    record_checkpoint(repo_root, summary, next_action, collect_git_details(repo_root), validation=None)
    return {
        "auto_recorded": True,
        "auto_started": auto_started,
        "summary": summary,
        "task": task,
        "next_action": next_action,
    }
