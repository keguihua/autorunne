from __future__ import annotations

from pathlib import Path

from autorunne.commands.finish import FinishValidationError, _resolve_validation_command, _run_validation
from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import collect_git_details, record_checkpoint


def run(
    target: Path,
    summary: str,
    next_action: str | None = None,
    validation_command: str | None = None,
    skip_validation: bool = False,
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne checkpoint must run inside an existing git repository")

    clean_summary = summary.strip()
    resolved_next_action = next_action.strip() if next_action else clean_summary
    resolved_validation_command = _resolve_validation_command(repo_root, validation_command, skip_validation)
    validation = _run_validation(repo_root, resolved_validation_command)
    record_checkpoint(repo_root, clean_summary, resolved_next_action, collect_git_details(repo_root), validation=validation)
    return {
        "repo_root": str(repo_root),
        "summary": clean_summary,
        "next_action": resolved_next_action,
        "validation": validation,
    }
