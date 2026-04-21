from __future__ import annotations

import time
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.filewatch import diff_snapshots, snapshot_tree
from autorunne.commands import sync as sync_cmd


def run(target: Path, duration: float = 30.0, interval: float = 1.0) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne watch must run inside an existing git repository")

    start = time.time()
    previous = snapshot_tree(repo_root)
    changes = 0
    last_sync = None
    last_changed_files: list[str] = []

    while time.time() - start < duration:
        time.sleep(interval)
        current = snapshot_tree(repo_root)
        if current != previous:
            changes += 1
            last_changed_files = diff_snapshots(previous, current)
            sync_result = sync_cmd.run(repo_root)
            last_sync = sync_result["repo_root"]
            previous = current
        else:
            previous = current

    return {
        "repo_root": str(repo_root),
        "changes_detected": changes,
        "last_sync": last_sync,
        "last_changed_files": last_changed_files,
        "duration": duration,
    }
