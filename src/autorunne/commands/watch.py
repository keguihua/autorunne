from __future__ import annotations

import time
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.commands import sync as sync_cmd


SKIP_DIRS = {".git", ".autorunne", ".dist-release", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}


def _snapshot(repo_root: Path) -> dict[str, float]:
    snapshot: dict[str, float] = {}
    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        snapshot[str(path.relative_to(repo_root))] = path.stat().st_mtime
    return snapshot


def run(target: Path, duration: float = 30.0, interval: float = 1.0) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne watch must run inside an existing git repository")

    start = time.time()
    previous = _snapshot(repo_root)
    changes = 0
    last_sync = None

    while time.time() - start < duration:
        time.sleep(interval)
        current = _snapshot(repo_root)
        if current != previous:
            changes += 1
            sync_result = sync_cmd.run(repo_root)
            last_sync = sync_result["repo_root"]
            previous = current
        else:
            previous = current

    return {
        "repo_root": str(repo_root),
        "changes_detected": changes,
        "last_sync": last_sync,
        "duration": duration,
    }
