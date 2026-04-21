from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.state_engine import sync_workspace


def run(target: Path, note: str | None = None, action: str = "workspace_synced") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne sync must run inside an existing git repository")
    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    state = sync_workspace(repo_root, scan, action=action, note=note)
    scan["next_action"] = state["current"]["next_action"]
    return {"repo_root": str(repo_root), "scan": scan}
