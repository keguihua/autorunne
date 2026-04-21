from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import render_from_state, workflow_exists


def run(target: Path) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne render must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne render requires an initialized Autorunne workspace")
    return render_from_state(repo_root)
