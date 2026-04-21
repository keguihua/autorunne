from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root, ensure_local_exclude, is_tracked
from autorunne.core.paths import workflow_dir
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.state_engine import workflow_exists, workflow_needs_migration, workflow_summary
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

    if workflow_exists(repo_root):
        state_summary = workflow_summary(repo_root)
        summary.update(
            {
                "next_action": state_summary["next_action"] or scan["next_action"],
                "active_task": state_summary["active_task"],
                "last_action": state_summary["last_action"],
                "updated_at": state_summary["updated_at"],
                "task_counts": state_summary["task_counts"],
                "session_count": state_summary["session_count"],
                "event_count": state_summary["event_count"],
                "repo_integrations": state_summary["repo_integrations"],
                "workflow_mode": "state",
            }
        )
    elif workflow_needs_migration(repo_root):
        summary.update(
            {
                "workflow_mode": "legacy",
                "legacy_workspace": True,
                "resume_hint": "Legacy workspace detected. Run `autorunne migrate` to convert markdown memory into state files.",
                "next_action": "Run `autorunne migrate`, then continue from the imported next action.",
            }
        )
    else:
        summary.update(
            {
                "workflow_mode": "scan",
                "legacy_workspace": False,
                "active_task": None,
                "last_action": None,
                "updated_at": None,
                "task_counts": {"completed": 0, "in_progress": 0, "next_up": 0, "known_unknowns": 0},
                "session_count": 0,
                "event_count": 0,
                "repo_integrations": {},
            }
        )
    return summary
