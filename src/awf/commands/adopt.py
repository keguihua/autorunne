from __future__ import annotations

from pathlib import Path

from awf.core.gitops import detect_repo_root, ensure_local_exclude
from awf.core.paths import save_config
from awf.core.scanner import recommend_next_action, scan_repo
from awf.core.templater import render_bundle
from awf.core.writer import write_workflow_files
from awf.models.config import WorkflowConfig


def run(target: Path) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("awf adopt must run inside an existing git repository")
    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    write_workflow_files(repo_root, render_bundle(scan, mode="adopt"), scan)
    save_config(repo_root, WorkflowConfig())
    exclude_path = ensure_local_exclude(repo_root)
    return {"repo_root": str(repo_root), "exclude_path": str(exclude_path), "scan": scan}
