from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import start_task


def run(target: Path, task: str, next_action: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne start must run inside an existing git repository")

    clean_task = task.strip()
    resolved_next_action = next_action.strip() if next_action else clean_task
    start_task(repo_root, clean_task, resolved_next_action)
    return {
        "repo_root": str(repo_root),
        "task": clean_task,
        "next_action": resolved_next_action,
    }
