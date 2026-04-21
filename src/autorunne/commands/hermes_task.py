from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autorunne.commands import open as open_cmd
from autorunne.commands import start as start_cmd
from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file
from autorunne.commands.finish import _append_decision


_DECISIONS_FALLBACK = """# Decisions

## Recorded decisions
"""


def run(
    target: Path,
    task: str,
    next_action: str | None = None,
    context: str | None = None,
    decision: str | None = None,
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne hermes-task must run inside an existing git repository")

    open_result = open_cmd.run(repo_root)
    start_result = start_cmd.run(repo_root, task=task, next_action=next_action)

    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")
    decisions_path = workflow_file(repo_root, "DECISIONS.md")
    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    log_lines = [
        f"\n## {timestamp} | hermes task ingress",
        f"- Source: hermes",
        f"- Task: {task.strip()}",
        f"- Next action: {start_result['next_action']}",
        f"- Workspace action: {open_result['action']}",
    ]
    if context and context.strip():
        log_lines.append(f"- Context: {context.strip()}")
    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(log_lines) + "\n", encoding="utf-8")

    if decision and decision.strip():
        existing_decisions = decisions_path.read_text(encoding="utf-8") if decisions_path.exists() else _DECISIONS_FALLBACK
        updated_decisions = _append_decision(existing_decisions, decision.strip(), timestamp)
        decisions_path.write_text(updated_decisions.rstrip() + "\n", encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "task": task.strip(),
        "next_action": start_result["next_action"],
        "workspace_action": open_result["action"],
        "context": context.strip() if context and context.strip() else None,
        "decision": decision.strip() if decision and decision.strip() else None,
    }
