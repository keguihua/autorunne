from __future__ import annotations

from pathlib import Path

from autorunne.commands import open as open_cmd
from autorunne.commands import start as start_cmd
from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import record_task_ingress


def run(
    target: Path,
    task: str,
    source: str = "hermes",
    next_action: str | None = None,
    context: str | None = None,
    decision: str | None = None,
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne hermes-task must run inside an existing git repository")

    open_result = open_cmd.run(repo_root)
    start_result = start_cmd.run(repo_root, task=task, next_action=next_action)
    clean_source = source.strip() if source and source.strip() else "agent"
    record_task_ingress(
        repo_root,
        source=clean_source,
        task=task,
        next_action=start_result["next_action"],
        workspace_action=open_result["action"],
        context=context,
        decision=decision,
    )

    return {
        "repo_root": str(repo_root),
        "source": clean_source,
        "task": task.strip(),
        "next_action": start_result["next_action"],
        "workspace_action": open_result["action"],
        "context": context.strip() if context and context.strip() else None,
        "decision": decision.strip() if decision and decision.strip() else None,
    }
