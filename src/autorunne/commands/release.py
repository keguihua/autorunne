from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.release import create_release_bundle


def run(target: Path, version: str, skip_build: bool = False) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne release must run inside an existing git repository")
    return create_release_bundle(repo_root, version=version, build_packages=not skip_build)
