from __future__ import annotations

import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autorunne.core.paths import (
    STATE_FILES,
    read_json,
    state_file,
    workflow_dir,
    workflow_file,
    write_json,
)
from autorunne.core.templater import render_agent_compat_bundle, render_view_bundle
from autorunne.core.writer import ensure_workflow_layout, write_agent_compat_files, write_rendered_views, write_snapshot


def utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _task_item(text: str, *, status: str = "pending", timestamp: str | None = None, source: str = "autorunne") -> dict[str, str]:
    return {
        "text": text.strip(),
        "status": status,
        "timestamp": timestamp or utc_now(),
        "source": source,
    }


def _dedupe_tasks(items: list[dict[str, str]]) -> list[dict[str, str]]:
    seen: set[str] = set()
    ordered: list[dict[str, str]] = []
    for item in items:
        key = item.get("text", "").strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        ordered.append(item)
    return ordered


def _remove_task(items: list[dict[str, str]], matcher: str) -> tuple[list[dict[str, str]], str | None]:
    lowered = matcher.strip().lower()
    kept = []
    matched = None
    for item in items:
        text = item.get("text", "").strip()
        if not matched and lowered and lowered in text.lower():
            matched = text
            continue
        kept.append(item)
    return kept, matched


def _git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def collect_git_details(repo_root: Path) -> dict[str, Any]:
    status_text = _git_output(repo_root, "status", "--short", "--untracked-files=all")
    diff_stat = _git_output(repo_root, "diff", "--stat")
    changed_files = []
    status_lines = []
    for raw_line in status_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        status_lines.append(line)
        path = line[3:].strip() if len(line) > 3 else line.strip()
        if path and path not in changed_files:
            changed_files.append(path)
    return {
        "git_status": status_lines,
        "diff_stat": diff_stat.splitlines() if diff_stat else [],
        "changed_files": changed_files,
    }


def _ensure_event_file(repo_root: Path) -> Path:
    path = state_file(repo_root, "events.jsonl")
    if not path.exists():
        path.write_text("", encoding="utf-8")
    return path


def append_event(repo_root: Path, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "timestamp": utc_now(),
        "type": event_type,
        "payload": payload,
    }
    ensure_workflow_layout(repo_root)
    path = _ensure_event_file(repo_root)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")
    return event


def load_events(repo_root: Path) -> list[dict[str, Any]]:
    path = _ensure_event_file(repo_root)
    events = []
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        events.append(json.loads(stripped))
    return events


def _seed_state(repo_root: Path, scan: dict[str, Any], action: str) -> dict[str, Any]:
    timestamp = utc_now()
    current = {
        "repo_name": scan["repo_name"],
        "repo_root": str(repo_root),
        "stack": scan["stack"],
        "framework": scan["framework"],
        "package_manager": scan["package_manager"],
        "important_files": scan["important_files"],
        "source_dirs": scan["source_dirs"],
        "commands": scan["commands"],
        "tracked_files_count": scan["tracked_files_count"],
        "recent_files": scan["recent_files"],
        "recent_commits": scan["recent_commits"],
        "project_phase": scan["project_phase"],
        "resume_hint": scan["resume_hint"],
        "next_action": scan["next_action"],
        "active_task": None,
        "created_at": timestamp,
        "updated_at": timestamp,
        "last_action": action,
        "integrations": {
            "repo": {"tools": [], "wrappers": [], "updated_at": None},
            "user": {"tools": [], "wrappers": [], "updated_at": None},
        },
    }
    tasks = {
        "completed": _dedupe_tasks(
            [
                _task_item(f"Detected stack: {', '.join(scan['stack'])}", status="completed", timestamp=timestamp, source="scan"),
                _task_item(
                    f"Detected framework: {', '.join(scan['framework'])}",
                    status="completed",
                    timestamp=timestamp,
                    source="scan",
                ),
                _task_item(
                    f"Detected package manager: {', '.join(scan['package_manager'])}",
                    status="completed",
                    timestamp=timestamp,
                    source="scan",
                ),
                _task_item(f"Detected project phase: {scan['project_phase']}", status="completed", timestamp=timestamp, source="scan"),
            ]
        ),
        "in_progress": [],
        "next_up": [_task_item(scan["next_action"], timestamp=timestamp, source="scan")],
        "known_unknowns": [
            _task_item("Confirm deployment flow", timestamp=timestamp, source="bootstrap"),
            _task_item("Confirm protected or high-risk modules before large edits", timestamp=timestamp, source="bootstrap"),
        ],
    }
    decisions = {
        "baseline": [
            f"Project detected as: {', '.join(scan['stack'])}",
            f"Main framework likely: {', '.join(scan['framework'])}",
            f"Package manager likely: {', '.join(scan['package_manager'])}",
            f"Project phase likely: {scan['project_phase']}",
        ],
        "items": [],
    }
    sessions = {"items": []}
    return {"current": current, "tasks": tasks, "decisions": decisions, "sessions": sessions}


def _read_legacy_text(repo_root: Path, name: str) -> str:
    path = workflow_file(repo_root, name)
    return path.read_text(encoding="utf-8") if path.exists() else ""


def _extract_legacy_section(content: str, heading: str) -> list[str]:
    pattern = rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, content)
    if not match:
        return []
    return [line.strip() for line in match.group(1).splitlines() if line.strip().startswith("-")]


def _import_legacy_views(repo_root: Path, state: dict[str, Any]) -> dict[str, Any]:
    next_action_text = _read_legacy_text(repo_root, "NEXT_ACTION.md")
    next_lines = [line.strip() for line in next_action_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if next_lines:
        state["current"]["next_action"] = next_lines[-1]
        state["tasks"]["next_up"] = [_task_item(next_lines[-1], source="legacy-import")]

    tasks_text = _read_legacy_text(repo_root, "TASKS.md")
    if tasks_text:
        completed = [
            _task_item(line.split("]", 1)[-1].strip(), status="completed", source="legacy-import")
            for line in _extract_legacy_section(tasks_text, "Completed / inferred")
        ]
        in_progress = [
            _task_item(line.split("]", 1)[-1].strip(), source="legacy-import")
            for line in _extract_legacy_section(tasks_text, "In progress")
        ]
        next_up = [
            _task_item(line.split("]", 1)[-1].strip(), source="legacy-import")
            for line in _extract_legacy_section(tasks_text, "Next up")
        ]
        known_unknowns = [
            _task_item(line.split("]", 1)[-1].strip(), source="legacy-import")
            for line in _extract_legacy_section(tasks_text, "Known unknowns")
        ]
        if completed:
            state["tasks"]["completed"] = _dedupe_tasks(completed + state["tasks"].get("completed", []))
        if in_progress:
            state["tasks"]["in_progress"] = _dedupe_tasks(in_progress)
            state["current"]["active_task"] = in_progress[0]["text"]
        if next_up:
            state["tasks"]["next_up"] = _dedupe_tasks(next_up)
            state["current"]["next_action"] = next_up[0]["text"]
        if known_unknowns:
            state["tasks"]["known_unknowns"] = _dedupe_tasks(known_unknowns)

    decisions_text = _read_legacy_text(repo_root, "DECISIONS.md")
    if decisions_text:
        recorded = []
        for line in decisions_text.splitlines():
            stripped = line.strip()
            if stripped.startswith("-"):
                recorded.append({"timestamp": utc_now(), "text": stripped.lstrip("- ").strip(), "source": "legacy-import"})
        if recorded:
            state["decisions"]["items"] = recorded

    session_log = _read_legacy_text(repo_root, "SESSION_LOG.md")
    if session_log:
        state["sessions"]["items"].append(
            {
                "timestamp": utc_now(),
                "title": "legacy import",
                "lines": ["Imported existing markdown workflow into state."],
            }
        )
    return state


def workflow_exists(repo_root: Path) -> bool:
    return all(state_file(repo_root, name).exists() for name in STATE_FILES)


def load_workspace_state(repo_root: Path) -> dict[str, Any]:
    return {
        "current": read_json(state_file(repo_root, "current.json"), default={}),
        "tasks": read_json(state_file(repo_root, "tasks.json"), default={}),
        "decisions": read_json(state_file(repo_root, "decisions.json"), default={}),
        "sessions": read_json(state_file(repo_root, "sessions.json"), default={}),
        "events": load_events(repo_root),
    }


def save_workspace_state(repo_root: Path, state: dict[str, Any]) -> None:
    ensure_workflow_layout(repo_root)
    write_json(state_file(repo_root, "current.json"), state["current"])
    write_json(state_file(repo_root, "tasks.json"), state["tasks"])
    write_json(state_file(repo_root, "decisions.json"), state["decisions"])
    write_json(state_file(repo_root, "sessions.json"), state["sessions"])
    write_snapshot(
        repo_root,
        {
            "generated_at": state["current"].get("updated_at"),
            "repo_root": state["current"].get("repo_root"),
            "repo_name": state["current"].get("repo_name"),
            "workflow_root": str(workflow_dir(repo_root)),
            "state_files": STATE_FILES,
            "view_files": list(render_view_bundle(state).keys()),
            "last_action": state["current"].get("last_action"),
            "next_action": state["current"].get("next_action"),
            "integrations": state["current"].get("integrations", {}),
        },
    )


def render_views(repo_root: Path) -> dict[str, str]:
    state = load_workspace_state(repo_root)
    rendered = render_view_bundle(state)
    write_rendered_views(repo_root, rendered)
    write_agent_compat_files(repo_root, render_agent_compat_bundle())
    return rendered


def render_from_state(repo_root: Path) -> dict[str, Any]:
    rendered = render_views(repo_root)
    state = load_workspace_state(repo_root)
    return {"repo_root": str(repo_root), "rendered": list(rendered.keys()), "state": state}


def _touch_current_from_scan(current: dict[str, Any], scan: dict[str, Any], *, action: str) -> None:
    preserved_next_action = current.get("next_action")
    current.update(
        {
            "repo_name": scan["repo_name"],
            "repo_root": current.get("repo_root") or "",
            "stack": scan["stack"],
            "framework": scan["framework"],
            "package_manager": scan["package_manager"],
            "important_files": scan["important_files"],
            "source_dirs": scan["source_dirs"],
            "commands": scan["commands"],
            "tracked_files_count": scan["tracked_files_count"],
            "recent_files": scan["recent_files"],
            "recent_commits": scan["recent_commits"],
            "project_phase": scan["project_phase"],
            "resume_hint": scan["resume_hint"],
            "next_action": preserved_next_action or scan["next_action"],
            "last_action": action,
            "updated_at": utc_now(),
        }
    )


def _append_session(state: dict[str, Any], *, title: str, lines: list[str], timestamp: str | None = None) -> None:
    entry = {
        "timestamp": timestamp or utc_now(),
        "title": title,
        "lines": [line for line in lines if line],
    }
    state["sessions"].setdefault("items", []).append(entry)


def bootstrap_workspace(repo_root: Path, scan: dict[str, Any], *, action: str, note: str | None = None) -> dict[str, Any]:
    state = _seed_state(repo_root, scan, action)
    if workflow_dir(repo_root).exists():
        state = _import_legacy_views(repo_root, state)
    timestamp = utc_now()
    lines = [
        f"Mode: {action}",
        f"Repo: {scan['repo_name']}",
        f"Stack: {', '.join(scan['stack'])}",
        f"Framework: {', '.join(scan['framework'])}",
        f"Project phase: {scan['project_phase']}",
        f"Next action: {scan['next_action']}",
    ]
    if note:
        lines.append(f"Note: {note.strip()}")
    _append_session(state, title="workflow initialized", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, action, {"note": note, "scan": scan})
    render_views(repo_root)
    return state


def sync_workspace(repo_root: Path, scan: dict[str, Any], *, action: str, note: str | None = None) -> dict[str, Any]:
    if not workflow_exists(repo_root):
        return bootstrap_workspace(repo_root, scan, action=action, note=note)
    state = load_workspace_state(repo_root)
    current = state["current"]
    current["repo_root"] = str(repo_root)
    _touch_current_from_scan(current, scan, action=action)
    resolved_next_action = current.get("next_action") or scan["next_action"]
    next_item = _task_item(resolved_next_action, timestamp=current["updated_at"], source=action)
    state["tasks"]["next_up"] = _dedupe_tasks([next_item, *state["tasks"].get("next_up", [])])
    lines = [
        f"Stack: {', '.join(scan['stack'])}",
        f"Framework: {', '.join(scan['framework'])}",
        f"Next action: {resolved_next_action}",
    ]
    if note:
        lines.append(f"Note: {note.strip()}")
    title = "workspace open auto-resume" if action == "workspace_resumed" else "sync summary"
    _append_session(state, title=title, lines=lines, timestamp=current["updated_at"])
    save_workspace_state(repo_root, state)
    append_event(repo_root, action, {"note": note, "scan": scan})
    render_views(repo_root)
    return state


def start_task(repo_root: Path, task: str, next_action: str) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    state["current"]["active_task"] = task.strip()
    state["current"]["next_action"] = next_action.strip()
    state["current"]["last_action"] = "task_started"
    state["current"]["updated_at"] = timestamp
    state["tasks"]["in_progress"] = _dedupe_tasks([_task_item(task, timestamp=timestamp, source="start"), *state["tasks"].get("in_progress", [])])
    state["tasks"]["next_up"] = _dedupe_tasks([_task_item(next_action, timestamp=timestamp, source="start"), *state["tasks"].get("next_up", [])])
    _append_session(state, title="start task", lines=[f"Task: {task.strip()}", f"Next action: {next_action.strip()}"], timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "task_started", {"task": task.strip(), "next_action": next_action.strip()})
    render_views(repo_root)
    return state


def record_checkpoint(
    repo_root: Path,
    summary: str,
    next_action: str,
    git_details: dict[str, Any],
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    state["current"]["next_action"] = next_action.strip()
    state["current"]["last_action"] = "checkpoint_recorded"
    state["current"]["updated_at"] = timestamp
    state["tasks"]["next_up"] = _dedupe_tasks([_task_item(next_action, timestamp=timestamp, source="checkpoint"), *state["tasks"].get("next_up", [])])
    lines = [
        f"Summary: {summary.strip()}",
        f"Next action: {next_action.strip()}",
        f"Changed files: {', '.join(git_details.get('changed_files', [])) or 'none'}",
        f"git_status: {' | '.join(git_details.get('git_status', [])) or 'clean'}",
        f"diff_stat: {' | '.join(git_details.get('diff_stat', [])) or 'none'}",
    ]
    payload = {"summary": summary.strip(), "next_action": next_action.strip(), **git_details}
    if validation:
        lines.append(f"Validation command: {validation['command']}")
        lines.append(f"Validation result: {validation['status']}")
        lines.append(f"validation: {validation}")
        payload["validation"] = validation
    _append_session(state, title="checkpoint", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "checkpoint_recorded", payload)
    render_views(repo_root)
    return state


def finish_task(
    repo_root: Path,
    *,
    summary: str,
    next_action: str,
    task_match: str | None,
    decision: str | None,
    git_details: dict[str, Any],
    validation: dict[str, Any] | None,
) -> tuple[dict[str, Any], str | None]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    matched = None
    in_progress = state["tasks"].get("in_progress", [])
    if task_match:
        in_progress, matched = _remove_task(in_progress, task_match)
    if not matched and state["current"].get("active_task"):
        in_progress, matched = _remove_task(in_progress, state["current"]["active_task"])
    state["tasks"]["in_progress"] = in_progress
    completed_text = matched or summary.strip()
    state["tasks"]["completed"] = _dedupe_tasks(
        [
            _task_item(completed_text, status="completed", timestamp=timestamp, source="finish"),
            *state["tasks"].get("completed", []),
        ]
    )
    next_up, _ = _remove_task(state["tasks"].get("next_up", []), completed_text)
    state["tasks"]["next_up"] = _dedupe_tasks([_task_item(next_action, timestamp=timestamp, source="finish"), *next_up])
    state["current"]["active_task"] = None if matched else state["current"].get("active_task")
    state["current"]["next_action"] = next_action.strip()
    state["current"]["last_action"] = "task_finished"
    state["current"]["updated_at"] = timestamp
    lines = [
        f"Summary: {summary.strip()}",
        f"Next action: {next_action.strip()}",
        f"Matched task: {matched}" if matched else "Matched task: none",
        f"Files changed: {', '.join(git_details.get('changed_files', [])) or 'none'}",
        f"git_status: {' | '.join(git_details.get('git_status', [])) or 'clean'}",
        f"diff_stat: {' | '.join(git_details.get('diff_stat', [])) or 'none'}",
    ]
    payload = {
        "summary": summary.strip(),
        "next_action": next_action.strip(),
        "matched_task": matched,
        **git_details,
    }
    if decision and decision.strip():
        clean_decision = decision.strip()
        state["decisions"].setdefault("items", []).append({"timestamp": timestamp, "text": clean_decision, "source": "finish"})
        lines.append(f"Decision: {clean_decision}")
        payload["decision"] = clean_decision
    if validation:
        lines.append(f"Validation command: {validation['command']}")
        lines.append(f"Validation result: {validation['status']}")
        lines.append(f"validation: {validation}")
        payload["validation"] = validation
    _append_session(state, title="finish summary", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "task_finished", payload)
    render_views(repo_root)
    return state, matched


def record_hermes_ingress(
    repo_root: Path,
    *,
    task: str,
    next_action: str,
    workspace_action: str,
    context: str | None,
    decision: str | None,
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    lines = [
        "Source: hermes",
        f"Task: {task.strip()}",
        f"Next action: {next_action.strip()}",
        f"Workspace action: {workspace_action}",
    ]
    payload: dict[str, Any] = {
        "task": task.strip(),
        "next_action": next_action.strip(),
        "workspace_action": workspace_action,
    }
    if context and context.strip():
        clean_context = context.strip()
        lines.append(f"Context: {clean_context}")
        payload["context"] = clean_context
    if decision and decision.strip():
        clean_decision = decision.strip()
        state["decisions"].setdefault("items", []).append({"timestamp": timestamp, "text": clean_decision, "source": "hermes"})
        lines.append(f"Decision: {clean_decision}")
        payload["decision"] = clean_decision
    _append_session(state, title="hermes task ingress", lines=lines, timestamp=timestamp)
    state["current"]["updated_at"] = timestamp
    state["current"]["last_action"] = "hermes_task_ingressed"
    save_workspace_state(repo_root, state)
    append_event(repo_root, "hermes_task_ingressed", payload)
    render_views(repo_root)
    return state


def record_integration(repo_root: Path, *, scope: str, tools: list[str], wrappers: list[str], action: str) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    bucket = state["current"].setdefault("integrations", {}).setdefault(scope, {"tools": [], "wrappers": [], "updated_at": None})
    bucket["tools"] = sorted(set(bucket.get("tools", []) + tools))
    bucket["wrappers"] = sorted(set(bucket.get("wrappers", []) + wrappers))
    bucket["updated_at"] = timestamp
    state["current"]["updated_at"] = timestamp
    state["current"]["last_action"] = action
    _append_session(
        state,
        title="integration installed" if action == "integration_installed" else "integration updated",
        lines=[f"Scope: {scope}", f"Tools: {', '.join(tools)}", f"Wrappers: {', '.join(wrappers) or 'none'}"],
        timestamp=timestamp,
    )
    save_workspace_state(repo_root, state)
    append_event(repo_root, action, {"scope": scope, "tools": tools, "wrappers": wrappers})
    render_views(repo_root)
    return state


def manual_record(
    repo_root: Path,
    *,
    summary: str,
    next_action: str | None = None,
    task: str | None = None,
    decision: str | None = None,
    event_type: str = "manual_recorded",
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    clean_summary = summary.strip()
    resolved_next = next_action.strip() if next_action else state["current"].get("next_action") or clean_summary
    state["current"]["next_action"] = resolved_next
    state["current"]["updated_at"] = timestamp
    state["current"]["last_action"] = event_type
    lines = [f"Summary: {clean_summary}", f"Next action: {resolved_next}"]
    payload: dict[str, Any] = {"summary": clean_summary, "next_action": resolved_next}
    if task and task.strip():
        clean_task = task.strip()
        state["tasks"]["next_up"] = _dedupe_tasks([_task_item(clean_task, timestamp=timestamp, source="record"), *state["tasks"].get("next_up", [])])
        lines.append(f"Task: {clean_task}")
        payload["task"] = clean_task
    if decision and decision.strip():
        clean_decision = decision.strip()
        state["decisions"].setdefault("items", []).append({"timestamp": timestamp, "text": clean_decision, "source": "record"})
        lines.append(f"Decision: {clean_decision}")
        payload["decision"] = clean_decision
    _append_session(state, title="manual record", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, event_type, payload)
    render_views(repo_root)
    return {"state": state, "payload": payload}


def trace_events(repo_root: Path, *, limit: int = 20, event_type: str | None = None) -> list[dict[str, Any]]:
    events = load_events(repo_root)
    if event_type:
        events = [item for item in events if item.get("type") == event_type]
    return events[-limit:]


def session_history(repo_root: Path, *, limit: int = 20) -> list[dict[str, Any]]:
    sessions = load_workspace_state(repo_root)["sessions"].get("items", [])
    return sessions[-limit:]


def show_section(repo_root: Path, *, section: str = "all") -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    mapping = {
        "current": state["current"],
        "tasks": state["tasks"],
        "decisions": state["decisions"],
        "sessions": state["sessions"],
        "events": state["events"],
    }
    if section == "all":
        return {"current": state["current"], "tasks": state["tasks"], "decisions": state["decisions"], "sessions": state["sessions"], "events": state["events"]}
    if section not in mapping:
        raise ValueError(f"Unsupported section: {section}")
    return {section: mapping[section]}
