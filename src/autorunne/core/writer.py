from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import (
    agents_dir,
    ensure_dir,
    snapshot_file,
    state_dir,
    view_file,
    views_dir,
    workflow_file,
    write_json,
    write_text,
)


def ensure_workflow_layout(repo_root: Path) -> None:
    ensure_dir(state_dir(repo_root))
    ensure_dir(views_dir(repo_root))
    ensure_dir(agents_dir(repo_root))
    ensure_dir(snapshot_file(repo_root).parent)


def write_rendered_views(repo_root: Path, rendered: dict[str, str]) -> None:
    ensure_workflow_layout(repo_root)
    for relative_name, content in rendered.items():
        write_text(view_file(repo_root, relative_name), content)
        write_text(workflow_file(repo_root, relative_name), content)


def write_agent_compat_files(repo_root: Path, rendered: dict[str, str]) -> None:
    ensure_workflow_layout(repo_root)
    for relative_name, content in rendered.items():
        write_text(agents_dir(repo_root) / relative_name, content)


def write_snapshot(repo_root: Path, payload: dict) -> None:
    ensure_workflow_layout(repo_root)
    write_json(snapshot_file(repo_root), payload)
