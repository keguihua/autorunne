from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import workflow_exists, session_history


def run(target: Path, *, limit: int = 20) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne history must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne history requires an initialized Autorunne workspace")
    items = session_history(repo_root, limit=limit)
    return {"repo_root": str(repo_root), "items": items}
