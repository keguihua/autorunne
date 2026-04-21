from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import ensure_dir, workflow_dir, write_json, write_text

PRESERVE_EXISTING_FILES = {
    "PROJECT_CONTEXT.md",
    "TASKS.md",
    "DECISIONS.md",
    "SESSION_LOG.md",
    "RULES.md",
    "NEXT_ACTION.md",
    "agents/common.md",
    "agents/claude-code.md",
    "agents/codex.md",
    "agents/hermes.md",
    "agents/cursor.md",
    "agents/copilot.md",
}


def write_workflow_files(repo_root: Path, rendered: dict[str, str], snapshot: dict) -> None:
    root = workflow_dir(repo_root)
    ensure_dir(root)
    ensure_dir(root / "agents")
    ensure_dir(root / "snapshots")
    for relative_name, content in rendered.items():
        target = root / relative_name
        if relative_name in PRESERVE_EXISTING_FILES and target.exists():
            continue
        write_text(target, content)
    write_json(root / "snapshots" / "latest.json", snapshot)
