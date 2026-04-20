from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.templater import render_bundle
from autorunne.core.writer import write_workflow_files


def _append_sync_summary(repo_root: Path, scan: dict, note: str | None = None) -> None:
    log_path = workflow_file(repo_root, "SESSION_LOG.md")
    existing = log_path.read_text(encoding="utf-8") if log_path.exists() else "# Session Log\n"
    timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')
    lines = [
        f"\n## {timestamp} | sync summary",
        f"- Stack: {', '.join(scan['stack'])}",
        f"- Framework: {', '.join(scan['framework'])}",
        f"- Next action: {scan['next_action']}",
    ]
    if note:
        lines.append(f"- Note: {note.strip()}")
    log_path.write_text(existing.rstrip() + "\n" + "\n".join(lines) + "\n", encoding="utf-8")


def run(target: Path, note: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne sync must run inside an existing git repository")
    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    rendered = render_bundle(scan, mode="sync")
    rendered.pop("SESSION_LOG.md", None)
    write_workflow_files(repo_root, rendered, scan)
    _append_sync_summary(repo_root, scan, note=note)
    return {"repo_root": str(repo_root), "scan": scan}
