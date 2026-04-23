from __future__ import annotations

from pathlib import Path

from autorunne.commands import finish as finish_cmd
from autorunne.core.paths import load_config
from autorunne.core.scanner import scan_repo
from autorunne.core.state_engine import collect_git_details, finish_task, load_workspace_state, record_checkpoint, start_task, workflow_exists

_GENERIC_AUTO_TASK_PREFIX = "Review and continue the latest local changes in "
_DOC_EXTENSIONS = {".md", ".txt", ".rst", ".adoc"}


def _compact_file_summary(changed_files: list[str], limit: int = 3) -> str:
    if not changed_files:
        return "the latest local changes"
    head = changed_files[:limit]
    summary = ", ".join(head)
    remaining = len(changed_files) - len(head)
    if remaining > 0:
        summary += f" (+{remaining} more)"
    return summary


def _is_ignored_path(path: str, ignored_paths: list[str]) -> bool:
    normalized = path.strip().strip("/")
    if not normalized:
        return True
    for ignored in ignored_paths:
        clean = ignored.strip().strip("/")
        if not clean:
            continue
        if normalized == clean or normalized.startswith(f"{clean}/"):
            return True
    return False


def filter_recordable_files(repo_root: Path, changed_files: list[str]) -> list[str]:
    config = load_config(repo_root)
    filtered: list[str] = []
    for path in changed_files:
        if _is_ignored_path(path, config.auto_record_ignored_paths):
            continue
        filtered.append(path)
    return filtered


def auto_record_local_change(repo_root: Path, *, changed_files: list[str], source: str) -> dict[str, object]:
    if not changed_files or not workflow_exists(repo_root):
        return {"auto_recorded": False, "auto_started": False, "summary": None, "task": None, "changed_files": []}

    config = load_config(repo_root)
    if not config.auto_record_on_change:
        return {"auto_recorded": False, "auto_started": False, "summary": None, "task": None, "changed_files": []}

    meaningful_files = filter_recordable_files(repo_root, changed_files)
    if not meaningful_files:
        return {"auto_recorded": False, "auto_started": False, "summary": None, "task": None, "changed_files": []}

    state = load_workspace_state(repo_root)
    current = state["current"]
    active_task = (current.get("active_task") or "").strip()
    file_summary = _compact_file_summary(meaningful_files)
    next_action = (current.get("next_action") or f"Review and continue the latest local changes in {file_summary}.").strip()

    auto_started = False
    task = active_task or None
    if not active_task:
        task = f"Review and continue the latest local changes in {file_summary}"
        start_task(repo_root, task, next_action)
        auto_started = True

    git_details = collect_git_details(repo_root)
    git_details["changed_files"] = meaningful_files
    summary = f"Auto-recorded local changes via {source}: {_compact_file_summary(meaningful_files, limit=5)}"
    record_checkpoint(repo_root, summary, next_action, git_details, validation=None)
    return {
        "auto_recorded": True,
        "auto_started": auto_started,
        "summary": summary,
        "task": task,
        "next_action": next_action,
        "changed_files": meaningful_files,
    }


def _is_doc_only_change(changed_files: list[str]) -> bool:
    return bool(changed_files) and all(Path(path).suffix.lower() in _DOC_EXTENSIONS for path in changed_files)


def auto_finish_active_task(repo_root: Path, *, source: str) -> dict[str, object]:
    if not workflow_exists(repo_root):
        return {"finished": False, "reason": "workflow-missing", "task": None}

    state = load_workspace_state(repo_root)
    current = state.get("current", {})
    active_task = (current.get("active_task") or "").strip()
    if not active_task:
        return {"finished": False, "reason": "no-active-task", "task": None}
    if active_task.startswith(_GENERIC_AUTO_TASK_PREFIX):
        return {"finished": False, "reason": "generic-auto-task", "task": active_task}

    git_details = collect_git_details(repo_root)
    meaningful_files = filter_recordable_files(repo_root, git_details.get("changed_files", []))
    if not meaningful_files:
        return {"finished": False, "reason": "no-meaningful-changes", "task": active_task}

    current_next = (current.get("next_action") or "").strip()
    scanned_next = (scan_repo(repo_root).get("next_action") or current_next or "Confirm the next concrete step.").strip()
    if scanned_next == current_next:
        next_action = "Review the completed changes and choose the next concrete slice."
    else:
        next_action = scanned_next
    summary = f"Auto-finished task after {source}: {active_task}"
    validation_command = finish_cmd._resolve_validation_command(
        repo_root,
        validation_command=None,
        skip_validation=_is_doc_only_change(meaningful_files),
    )
    validation = finish_cmd._run_validation(repo_root, validation_command)
    filtered_git_details = {
        **git_details,
        "changed_files": meaningful_files,
        "git_status": [
            line
            for line in git_details.get("git_status", [])
            if any(path in line for path in meaningful_files)
        ],
    }
    _, matched_task = finish_task(
        repo_root,
        summary=summary,
        next_action=next_action,
        task_match=active_task,
        decision=None,
        git_details=filtered_git_details,
        validation=validation,
    )
    return {
        "finished": True,
        "reason": "auto-finished",
        "task": active_task,
        "matched_task": matched_task,
        "summary": summary,
        "next_action": next_action,
        "changed_files": meaningful_files,
        "validation": validation,
    }
