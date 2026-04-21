from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import view_file
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.state_engine import migrate_legacy_workspace, workflow_exists, workflow_needs_migration


def run(target: Path, *, note: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne migrate must run inside an existing git repository")
    if workflow_exists(repo_root) and not workflow_needs_migration(repo_root):
        return {
            "repo_root": str(repo_root),
            "migrated": False,
            "start_here_path": str(view_file(repo_root, "START_HERE.md")),
        }

    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    state = migrate_legacy_workspace(repo_root, scan, note=note)
    return {
        "repo_root": str(repo_root),
        "migrated": True,
        "next_action": state["current"]["next_action"],
        "start_here_path": str(view_file(repo_root, "START_HERE.md")),
    }
