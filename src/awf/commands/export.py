from __future__ import annotations

from pathlib import Path

from awf.core.exporter import export_clean_copy
from awf.core.gitops import detect_repo_root


def run(target: Path, output_name: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("awf export must run inside an existing git repository")
    exported = export_clean_copy(repo_root, output_name=output_name)
    return {"repo_root": str(repo_root), "exported_path": str(exported)}
