from __future__ import annotations

import subprocess
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import load_config, read_json, state_file
from autorunne.core.scanner import scan_repo
from autorunne.core.state_engine import collect_git_details, finish_task


class FinishValidationError(RuntimeError):
    def __init__(self, command: str, output: str):
        super().__init__(f"Validation failed: {command}")
        self.command = command
        self.output = output


def _read_current_next_action(repo_root: Path) -> str:
    current = read_json(state_file(repo_root, "current.json"), default={})
    return current.get("next_action") or "Confirm the next concrete step."


def _resolve_validation_command(repo_root: Path, validation_command: str | None, skip_validation: bool) -> str | None:
    if skip_validation:
        return None
    if validation_command and validation_command.strip():
        return validation_command.strip()
    config = load_config(repo_root)
    if not config.auto_validate_on_finish:
        return None
    scan = scan_repo(repo_root)
    detected = scan.get("commands", {}).get("test")
    return detected.strip() if detected else None


def _run_validation(repo_root: Path, command: str | None) -> dict | None:
    if not command:
        return None
    result = subprocess.run(command, cwd=repo_root, shell=True, capture_output=True, text=True)
    combined_output = "\n".join(part for part in [result.stdout.strip(), result.stderr.strip()] if part).strip()
    if result.returncode != 0:
        raise FinishValidationError(command, combined_output)
    return {"command": command, "status": "passed", "output": combined_output}


def run(
    target: Path,
    summary: str,
    next_action: str | None = None,
    task_match: str | None = None,
    decision: str | None = None,
    validation_command: str | None = None,
    skip_validation: bool = False,
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne finish must run inside an existing git repository")

    clean_summary = summary.strip()
    resolved_next_action = next_action.strip() if next_action else _read_current_next_action(repo_root)
    resolved_validation_command = _resolve_validation_command(repo_root, validation_command, skip_validation)
    validation = _run_validation(repo_root, resolved_validation_command)
    git_details = collect_git_details(repo_root)
    _, matched_task = finish_task(
        repo_root,
        summary=clean_summary,
        next_action=resolved_next_action,
        task_match=task_match,
        decision=decision,
        git_details=git_details,
        validation=validation,
    )

    return {
        "repo_root": str(repo_root),
        "summary": clean_summary,
        "next_action": resolved_next_action,
        "matched_task": matched_task,
        "decision": decision.strip() if decision else None,
        "changed_files": git_details["changed_files"],
        "validation": validation,
    }
