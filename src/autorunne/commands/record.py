from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import manual_record, workflow_exists


def run(
    target: Path,
    *,
    summary: str,
    next_action: str | None = None,
    task: str | None = None,
    decision: str | None = None,
    event_type: str = "manual_recorded",
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne record must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne record requires an initialized Autorunne workspace")
    result = manual_record(
        repo_root,
        summary=summary,
        next_action=next_action,
        task=task,
        decision=decision,
        event_type=event_type,
    )
    return {
        "repo_root": str(repo_root),
        "summary": summary.strip(),
        "next_action": result["payload"]["next_action"],
        "task": result["payload"].get("task"),
        "decision": result["payload"].get("decision"),
        "event_type": event_type,
    }
