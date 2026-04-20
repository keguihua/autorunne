from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file


def run(target: Path, summary: str, next_action: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne finish must run inside an existing git repository")

    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")
    next_action_path = workflow_file(repo_root, "NEXT_ACTION.md")

    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"
    existing_next_action = next_action_path.read_text(encoding="utf-8") if next_action_path.exists() else "# Next Action\n\nConfirm the next concrete step.\n"

    resolved_next_action = next_action.strip() if next_action else existing_next_action.splitlines()[-1].strip()
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    entry_lines = [
        f"\n## {timestamp} | finish summary",
        f"- Summary: {summary.strip()}",
        f"- Next action: {resolved_next_action}",
    ]
    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(entry_lines) + "\n", encoding="utf-8")
    next_action_path.write_text(f"# Next Action\n\n{resolved_next_action}\n", encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "summary": summary.strip(),
        "next_action": resolved_next_action,
    }
