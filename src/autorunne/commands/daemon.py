from __future__ import annotations

import time
from pathlib import Path

from autorunne.commands import open as open_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.core.gitops import detect_repo_root

SKIP_DIRS = {".git", ".autorunne", ".dist-release", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}


def _snapshot(repo_root: Path) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        snapshot[str(path.relative_to(repo_root))] = path.stat().st_mtime_ns
    return snapshot


def run(target: Path, duration: float = 30.0, interval: float = 1.0) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne daemon must run inside an existing git repository")

    open_result = open_cmd.run(repo_root)
    previous = _snapshot(repo_root)
    start = time.time()
    ticks = 0
    syncs = 0
    last_sync = None

    while time.time() - start < duration:
        time.sleep(interval)
        ticks += 1
        current = _snapshot(repo_root)
        if current != previous:
            sync_result = sync_cmd.run(repo_root, note="daemon auto-sync")
            syncs += 1
            last_sync = sync_result["repo_root"]
            previous = current
        else:
            previous = current

    return {
        "repo_root": str(repo_root),
        "action": open_result["action"],
        "ticks": ticks,
        "syncs": syncs,
        "last_sync": last_sync,
        "next_action": open_result["scan"]["next_action"],
    }
