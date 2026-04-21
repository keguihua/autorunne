from __future__ import annotations

import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file

_TASKS_FALLBACK = """# Tasks

## Completed / inferred

## In progress
- [ ] Validate local run and test commands

## Next up
- [ ] Confirm the next concrete step.

## Known unknowns
- [ ] Confirm deployment flow
- [ ] Confirm protected or high-risk modules before large edits
"""

_DECISIONS_FALLBACK = """# Decisions

## Recorded decisions
"""

_OPEN_TASK_SECTIONS = ["In progress", "Next up", "Known unknowns"]


def _read_current_next_action(path: Path) -> str:
    if not path.exists():
        return "Confirm the next concrete step."
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        stripped = line.strip()
        if stripped and not stripped.startswith("#"):
            return stripped
    return "Confirm the next concrete step."


def _replace_tasks_section(content: str, heading: str, body_lines: list[str]) -> str:
    body = "\n".join(body_lines).strip()
    replacement = f"## {heading}\n{body}\n\n"
    pattern = rf"(?ms)^## {re.escape(heading)}\n.*?(?=^## |\Z)"
    if re.search(pattern, content):
        updated = re.sub(pattern, replacement, content, count=1)
    else:
        updated = content.rstrip() + "\n\n" + replacement
    return updated.rstrip() + "\n"


def _section_lines(content: str, heading: str) -> list[str]:
    pattern = rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content)
    if not match:
        return []
    return [line.rstrip() for line in match.group(1).splitlines() if line.strip()]


def _normalize_task_text(line: str) -> str:
    stripped = line.strip()
    stripped = re.sub(r"^- \[[ xX]\]\s*", "", stripped)
    stripped = re.sub(r"^-\s*", "", stripped)
    return stripped.strip()


def _append_completed_task(content: str, task_text: str) -> str:
    completed_line = f"- [x] {task_text}"
    existing_lines = _section_lines(content, "Completed / inferred")
    if completed_line not in existing_lines:
        existing_lines.append(completed_line)
    return _replace_tasks_section(content, "Completed / inferred", existing_lines)


def _pop_matching_open_task(content: str, matcher: str) -> tuple[str, str | None]:
    matched_task = None
    lowered = matcher.strip().lower()
    updated = content
    for heading in _OPEN_TASK_SECTIONS:
        lines = _section_lines(updated, heading)
        next_lines = []
        for line in lines:
            normalized = _normalize_task_text(line)
            is_open_task = line.strip().startswith("- [ ]")
            if not matched_task and is_open_task and lowered in normalized.lower():
                matched_task = normalized
                continue
            next_lines.append(line)
        updated = _replace_tasks_section(updated, heading, next_lines)
    return updated, matched_task


def _ensure_next_action(content: str, next_action: str) -> str:
    next_lines = _section_lines(content, "Next up")
    filtered = [line for line in next_lines if _normalize_task_text(line).lower() != next_action.lower()]
    return _replace_tasks_section(content, "Next up", [f"- [ ] {next_action}", *filtered])


def _append_decision(content: str, decision: str, timestamp: str) -> str:
    heading = "Recorded decisions"
    existing_lines = _section_lines(content, heading)
    decision_line = f"- {timestamp}: {decision.strip()}"
    if decision_line not in existing_lines:
        existing_lines.append(decision_line)
    return _replace_tasks_section(content, heading, existing_lines)


def _collect_changed_files(repo_root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "status", "--short", "--untracked-files=all"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=True,
    )
    files = []
    for raw_line in result.stdout.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        path = line[3:].strip()
        if path and path not in files:
            files.append(path)
    return files


def _update_tasks(content: str, summary: str, next_action: str, task_match: str | None = None) -> tuple[str, str | None]:
    updated = content
    matched_task = None
    if task_match:
        updated, matched_task = _pop_matching_open_task(updated, task_match)
    completed_text = matched_task or summary
    updated = _append_completed_task(updated, completed_text)
    updated = _ensure_next_action(updated, next_action)
    return updated, matched_task


def run(
    target: Path,
    summary: str,
    next_action: str | None = None,
    task_match: str | None = None,
    decision: str | None = None,
) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne finish must run inside an existing git repository")

    session_log_path = workflow_file(repo_root, "SESSION_LOG.md")
    next_action_path = workflow_file(repo_root, "NEXT_ACTION.md")
    tasks_path = workflow_file(repo_root, "TASKS.md")
    decisions_path = workflow_file(repo_root, "DECISIONS.md")

    clean_summary = summary.strip()
    existing_log = session_log_path.read_text(encoding="utf-8") if session_log_path.exists() else "# Session Log\n"
    resolved_next_action = next_action.strip() if next_action else _read_current_next_action(next_action_path)
    existing_tasks = tasks_path.read_text(encoding="utf-8") if tasks_path.exists() else _TASKS_FALLBACK
    existing_decisions = decisions_path.read_text(encoding="utf-8") if decisions_path.exists() else _DECISIONS_FALLBACK
    changed_files = _collect_changed_files(repo_root)

    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    updated_tasks, matched_task = _update_tasks(existing_tasks, clean_summary, resolved_next_action, task_match=task_match)
    entry_lines = [
        f"\n## {timestamp} | finish summary",
        f"- Summary: {clean_summary}",
        f"- Next action: {resolved_next_action}",
    ]
    if matched_task:
        entry_lines.append(f"- Matched task: {matched_task}")
    if decision:
        existing_decisions = _append_decision(existing_decisions, decision, timestamp)
        entry_lines.append(f"- Decision: {decision.strip()}")
    if changed_files:
        entry_lines.append(f"- Files changed: {', '.join(changed_files)}")

    session_log_path.write_text(existing_log.rstrip() + "\n" + "\n".join(entry_lines) + "\n", encoding="utf-8")
    next_action_path.write_text(f"# Next Action\n\n{resolved_next_action}\n", encoding="utf-8")
    tasks_path.write_text(updated_tasks, encoding="utf-8")
    decisions_path.write_text(existing_decisions.rstrip() + "\n", encoding="utf-8")

    return {
        "repo_root": str(repo_root),
        "summary": clean_summary,
        "next_action": resolved_next_action,
        "matched_task": matched_task,
        "decision": decision.strip() if decision else None,
        "changed_files": changed_files,
    }
