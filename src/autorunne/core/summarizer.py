from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import workflow_dir


def summarize_status(repo_root: Path, scan: dict) -> dict:
    root = workflow_dir(repo_root)
    expected = [
        "PROJECT_CONTEXT.md",
        "TASKS.md",
        "DECISIONS.md",
        "SESSION_LOG.md",
        "RULES.md",
        "NEXT_ACTION.md",
        "COMMANDS.md",
        "START_HERE.md",
        "config.json",
    ]
    present = [name for name in expected if (root / name).exists()]
    missing = [name for name in expected if name not in present]
    return {
        "repo": repo_root.name,
        "workflow_root": str(root),
        "present": present,
        "missing": missing,
        "stack": scan["stack"],
        "framework": scan["framework"],
        "next_action": scan["next_action"],
    }
