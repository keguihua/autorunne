from __future__ import annotations

from pathlib import Path

from autorunne.core.auto_record import auto_finish_active_task
from autorunne.core.gitops import detect_repo_root


def run(target: Path, *, source: str = "agent") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne auto-finish must run inside an existing git repository")

    result = auto_finish_active_task(repo_root, source=source)
    return {"repo_root": str(repo_root), **result}
