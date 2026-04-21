from __future__ import annotations

from pathlib import Path


DEFAULT_SKIP_DIRS = {".git", ".autorunne", ".dist-release", ".venv", "__pycache__", ".pytest_cache", "dist", "build"}


def snapshot_tree(repo_root: Path, skip_dirs: set[str] | None = None) -> dict[str, int]:
    ignored = skip_dirs or DEFAULT_SKIP_DIRS
    snapshot: dict[str, int] = {}
    for path in repo_root.rglob("*"):
        if path.is_dir():
            continue
        if any(part in ignored for part in path.parts):
            continue
        snapshot[str(path.relative_to(repo_root))] = path.stat().st_mtime_ns
    return snapshot


def diff_snapshots(previous: dict[str, int], current: dict[str, int]) -> list[str]:
    changed_paths = {
        path
        for path in set(previous) | set(current)
        if previous.get(path) != current.get(path)
    }
    return sorted(changed_paths)
