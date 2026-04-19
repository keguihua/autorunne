from __future__ import annotations

from pathlib import Path

from awf.core.gitops import detect_repo_root
from awf.core.vscode import install_vscode_integration


def run(target: Path) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("awf vscode must run inside an existing git repository")
    paths = install_vscode_integration(repo_root)
    return {"repo_root": str(repo_root), **paths}
