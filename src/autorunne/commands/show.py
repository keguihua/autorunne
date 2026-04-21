from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import show_section, workflow_exists


def run(target: Path, *, section: str = "all") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne show must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne show requires an initialized Autorunne workspace")
    return {"repo_root": str(repo_root), "section": section, "data": show_section(repo_root, section=section)}
