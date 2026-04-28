from __future__ import annotations

from pathlib import Path

from autorunne.commands import hermes_task as hermes_task_cmd


def run(
    target: Path,
    *,
    task: str,
    source: str = "agent",
    next_action: str | None = None,
    context: str | None = None,
    decision: str | None = None,
) -> dict:
    return hermes_task_cmd.run(
        target,
        task=task,
        source=source,
        next_action=next_action,
        context=context,
        decision=decision,
    )
