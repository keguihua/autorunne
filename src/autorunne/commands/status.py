from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root, ensure_local_exclude, is_tracked
from autorunne.core.paths import workflow_dir
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.summarizer import summarize_status


def run(target: Path) -> dict:
    repo_root = detect_repo_root(target) or target
    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    summary = summarize_status(repo_root, scan)
    summary["is_git_repo"] = (repo_root / ".git").exists()
    if summary["is_git_repo"]:
        summary["exclude_path"] = str(ensure_local_exclude(repo_root))
        summary["workflow_tracked"] = is_tracked(repo_root, str(workflow_dir(repo_root).name))
    else:
        summary["exclude_path"] = None
        summary["workflow_tracked"] = False
    return summary
