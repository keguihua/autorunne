from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import ensure_dir, workflow_dir, write_json, write_text


def write_workflow_files(repo_root: Path, rendered: dict[str, str], snapshot: dict) -> None:
    root = workflow_dir(repo_root)
    ensure_dir(root)
    ensure_dir(root / "agents")
    ensure_dir(root / "snapshots")
    for relative_name, content in rendered.items():
        write_text(root / relative_name, content)
    write_json(root / "snapshots" / "latest.json", snapshot)
