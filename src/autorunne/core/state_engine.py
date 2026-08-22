from __future__ import annotations

import json
import os
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autorunne import __version__ as AUTORUNNE_VERSION
from autorunne.core.paths import (
    STATE_FILES,
    read_json,
    state_file,
    view_file,
    workflow_dir,
    workflow_file,
    write_json,
    write_text,
)
from autorunne.core.mutation import state_mutator
from autorunne.core.persistence import read_jsonl_recovering, workspace_locked
from autorunne.core.templater import render_agent_compat_bundle, render_view_bundle
from autorunne.core.user_status import build_user_summary
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


def _refresh_next_up(
    items: list[dict[str, str]],
    *,
    next_action: str,
    timestamp: str,
    source: str,
    remove_texts: list[str] | None = None,
) -> list[dict[str, str]]:
    clean_next = next_action.strip()
    cleaned = list(items)
    for text in remove_texts or []:
        if text and text.strip():
            cleaned, _ = _remove_task(cleaned, text)
    kept = []
    for item in cleaned:
        text = (item.get("text") or "").strip()
        if text and _is_workflow_follow_up_text(text) and text.lower() != clean_next.lower():
            continue
        kept.append(item)
    return _dedupe_tasks([_task_item(clean_next, timestamp=timestamp, source=source), *kept])


def _realign_focus_sections(state: dict[str, Any], *, timestamp: str, source: str) -> None:
    active_task = (state.get("current", {}).get("active_task") or "").strip()
    in_progress = list(state.get("tasks", {}).get("in_progress", []))
    next_up = list(state.get("tasks", {}).get("next_up", []))

    keep_in_progress: list[dict[str, str]] = []
    demoted: list[dict[str, str]] = []

    if active_task:
        for item in in_progress:
            text = item.get("text", "").strip()
            if text.lower() == active_task.lower() and not keep_in_progress:
                keep_in_progress.append(item)
            else:
                demoted.append(item)
        if not keep_in_progress:
            keep_in_progress.append(_task_item(active_task, timestamp=timestamp, source=source))
        next_up, _ = _remove_task(next_up, active_task)
    else:
        demoted = in_progress

    state["tasks"]["in_progress"] = _dedupe_tasks(keep_in_progress)
    state["tasks"]["next_up"] = _dedupe_tasks([*demoted, *next_up])


def _parse_version_token(value: str | None) -> tuple[int, int, int] | None:
    if not value:
        return None
    match = re.search(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        return None
    return tuple(int(part) for part in match.groups())


def _is_release_backlog_text(text: str) -> bool:
    lowered = text.lower()
    release_terms = ("release", "publish", "pypi", "github", "tag ", "tag v", "ship ")
    return any(term in lowered for term in release_terms)


def _archive_stale_release_backlog(state: dict[str, Any], *, timestamp: str, source: str) -> list[str]:
    current_version = _parse_version_token(AUTORUNNE_VERSION)
    if not current_version:
        return []

    archived = list(state.get("tasks", {}).get("archived", []))
    kept_next_up: list[dict[str, str]] = []
    archived_texts: list[str] = []

    for item in state.get("tasks", {}).get("next_up", []):
        text = item.get("text", "").strip()
        item_version = _parse_version_token(text)
        if text and item_version and item_version < current_version and _is_release_backlog_text(text):
            archived.append(
                {
                    **item,
                    "status": "archived",
                    "timestamp": timestamp,
                    "source": source,
                }
            )
            archived_texts.append(text)
        else:
            kept_next_up.append(item)

    state["tasks"]["next_up"] = _dedupe_tasks(kept_next_up)
    state["tasks"]["archived"] = _dedupe_tasks(archived)
    return archived_texts


def _is_workflow_follow_up_text(text: str) -> bool:
    lowered = text.strip().lower()
    workflow_terms = (
        "workflow",
        "workflow follow-up",
        "status.md",
        "start_here.md",
        "next_action",
        "render",
        "renderer",
        "validation evidence",
        "public baseline",
        "current public baseline",
        "流程",
        "交接",
        "基线",
        "状态视图",
        "验证证据",
    )
    return any(term in lowered for term in workflow_terms)


def _is_placeholder_next_text(text: str) -> bool:
    clean = text.strip().lower()
    return clean in {
        "确认下一个具体任务",
        "确认下一个产品开发任务",
        "confirm the next concrete step.",
        "confirm the next concrete step",
        "confirm the next product development task.",
        "confirm the next product development task",
    }


_MISSING = object()


def _first_pending_product_task(state: dict[str, Any], *, exclude_texts: list[str | None]) -> str | None:
    excluded = {text.strip() for text in exclude_texts if text and text.strip()}
    for bucket in ("next_up", "in_progress"):
        for item in state.get("tasks", {}).get(bucket, []):
            text = (item.get("text") or "").strip()
            if not text or text in excluded or _is_workflow_follow_up_text(text) or _is_placeholder_next_text(text):
                continue
            return text
    return None


def _completed_task_texts(state: dict[str, Any]) -> set[str]:
    return {
        (item.get("text") or "").strip()
        for item in state.get("tasks", {}).get("completed", [])
        if (item.get("text") or "").strip()
    }


def _clean_next_slots(state: dict[str, Any]) -> bool:
    """Repair stale handoff focus fields before rendering user-facing views.

    Older workspaces can keep a completed task or workflow housekeeping note in
    `current.next_product_task`. Keep product and workflow lanes separated so the
    next agent sees a real product task, or `无` when none exists.
    """
    current = state.get("current", {})
    before = (current.get("next_action"), current.get("next_product_task"), current.get("workflow_follow_up"))

    completed = _completed_task_texts(state)
    current_product = (current.get("next_product_task") or "").strip()
    current_next = (current.get("next_action") or "").strip()
    workflow_follow_up = (current.get("workflow_follow_up") or "").strip()

    workflow_candidates = []
    for candidate in (workflow_follow_up, current_product, current_next):
        clean = (candidate or "").strip()
        if clean and clean != "无" and _is_workflow_follow_up_text(clean):
            workflow_candidates.append(clean)
    workflow_follow_up = workflow_candidates[0] if workflow_candidates else "无"

    product = current_product
    if current_next and current_next not in completed and not _is_workflow_follow_up_text(current_next) and not _is_placeholder_next_text(current_next):
        product = current_next
    elif not product or product in completed or _is_workflow_follow_up_text(product) or _is_placeholder_next_text(product):
        product = _first_pending_product_task(
            state,
            exclude_texts=[*completed, workflow_follow_up, current_next if _is_workflow_follow_up_text(current_next) else None],
        )

    current["next_product_task"] = product
    current["workflow_follow_up"] = workflow_follow_up or "无"
    if product:
        current["next_action"] = product
    elif current_next and current_next not in completed:
        current["next_action"] = current_next
    else:
        current["next_action"] = "确认下一个具体任务"

    after = (current.get("next_action"), current.get("next_product_task"), current.get("workflow_follow_up"))
    return before != after


def _set_next_slots(
    current: dict[str, Any],
    next_action: str,
    *,
    prefer_product: bool,
    product_fallback: str | None | object = _MISSING,
    exclude_product_texts: list[str | None] | None = None,
) -> None:
    clean_next = next_action.strip()
    excluded = {text.strip() for text in (exclude_product_texts or []) if text and text.strip()}
    explicit_product_fallback = product_fallback is not _MISSING
    if explicit_product_fallback:
        existing_product = (product_fallback or "").strip()  # type: ignore[union-attr]
    else:
        existing_product = (current.get("next_product_task") or current.get("next_action") or "").strip()
    if existing_product in excluded:
        existing_product = ""
    if clean_next and (not prefer_product) and _is_workflow_follow_up_text(clean_next):
        current["workflow_follow_up"] = clean_next
        current["next_product_task"] = existing_product or (None if explicit_product_fallback else "确认下一个产品开发任务")
        current["next_action"] = current["next_product_task"] or "确认下一个具体任务"
    else:
        current["next_product_task"] = clean_next
        current.setdefault("workflow_follow_up", "无")
        current["next_action"] = clean_next


def _structured_validation(validation: dict[str, Any] | None, *, timestamp: str) -> dict[str, str] | None:
    if not validation:
        return None
    return {
        "command": str(validation.get("command") or "").strip(),
        "status": str(validation.get("status") or "").strip(),
        "timestamp": timestamp,
        "output_summary": _summarize_validation_output(validation.get("output")),
    }


def _git_output(repo_root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=repo_root, capture_output=True, text=True)
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _classify_changed_file(path: str) -> str:
    clean = path.strip()
    if not clean:
        return "other"

    # Common cache / build / env directories that should never be treated as business code
    ignore_prefixes = (
        "__pycache__/",
        ".pytest_cache/",
        ".mypy_cache/",
        ".ruff_cache/",
        ".venv/",
        "venv/",
        "node_modules/",
        "dist/",
        "build/",
        ".eggs/",
        ".tox/",
    )
    if any(clean.startswith(p) for p in ignore_prefixes) or clean.endswith((".pyc", ".pyo", ".egg-info")):
        return "other"

    integration_prefixes = (
        ".agents/skills/autorunne-workflow/",
        ".claude/skills/autorunne-workflow/",
        ".cursor/rules/autorunne-workflow",
    )
    integration_files = {
        ".github/copilot-instructions.md",
        "AGENTS.md",
        "CLAUDE.md",
    }
    if clean.startswith(integration_prefixes) or clean in integration_files:
        return "integration"
    if clean.startswith(".autorunne/"):
        return "autorunne_state"
    return "business"


def classify_changed_files(changed_files: list[str]) -> dict[str, list[str]]:
    grouped = {"business": [], "autorunne_state": [], "integration": [], "other": []}
    for path in changed_files:
        bucket = _classify_changed_file(path)
        if path not in grouped[bucket]:
            grouped[bucket].append(path)
    return grouped


def collect_git_details(repo_root: Path) -> dict[str, Any]:
    status_text = _git_output(repo_root, "status", "--short", "--untracked-files=all")
    diff_stat = _git_output(repo_root, "diff", "--stat")
    raw_changed_files = []
    status_lines = []
    for raw_line in status_text.splitlines():
        line = raw_line.rstrip()
        if not line:
            continue
        status_lines.append(line)
        path = raw_line[3:].strip() if len(raw_line) > 3 and raw_line[2] == " " else raw_line[2:].strip() if len(raw_line) > 2 else line.strip()
        if path and path not in raw_changed_files:
            raw_changed_files.append(path)
    changed_files_by_type = classify_changed_files(raw_changed_files)
    return {
        "git_status": status_lines,
        "diff_stat": diff_stat.splitlines() if diff_stat else [],
        "raw_changed_files": raw_changed_files,
        "changed_files_by_type": changed_files_by_type,
        "changed_files": changed_files_by_type["business"],
    }


def _ensure_event_file(repo_root: Path) -> Path:
    path = state_file(repo_root, "events.jsonl")
    if not path.exists():
        write_text(path, "")
    return path


@workspace_locked
def append_event(repo_root: Path, event_type: str, payload: dict[str, Any]) -> dict[str, Any]:
    event = {
        "timestamp": utc_now(),
        "type": event_type,
        "payload": payload,
    }
    ensure_workflow_layout(repo_root)
    path = _ensure_event_file(repo_root)
    line = json.dumps(event, ensure_ascii=False) + "\n"
    with path.open("a", encoding="utf-8") as handle:
        handle.write(line)
        handle.flush()
        os.fsync(handle.fileno())
    return event


@workspace_locked
def load_events(repo_root: Path) -> list[dict[str, Any]]:
    return read_jsonl_recovering(state_file(repo_root, "events.jsonl"))


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
        "packages": scan.get("packages", []),
        "tracked_files_count": scan["tracked_files_count"],
        "recent_files": scan["recent_files"],
        "recent_commits": scan["recent_commits"],
        "project_phase": scan["project_phase"],
        "resume_hint": scan["resume_hint"],
        "next_action": scan["next_action"],
        "next_product_task": scan["next_action"],
        "workflow_follow_up": "无",
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
        "archived": [],
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
    state.setdefault("tasks", {}).setdefault("archived", [])
    next_action_text = _read_legacy_text(repo_root, "NEXT_ACTION.md")
    next_lines = [line.strip() for line in next_action_text.splitlines() if line.strip() and not line.strip().startswith("#")]
    if next_lines:
        state["current"]["next_action"] = next_lines[-1]
        state["current"]["next_product_task"] = next_lines[-1]
        state["current"].setdefault("workflow_follow_up", "无")
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
            state["current"]["next_product_task"] = next_up[0]["text"]
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


LEGACY_WORKFLOW_FILES = [
    "PROJECT_CONTEXT.md",
    "TASKS.md",
    "DECISIONS.md",
    "SESSION_LOG.md",
    "RULES.md",
    "NEXT_ACTION.md",
    "COMMANDS.md",
    "START_HERE.md",
]


def workflow_exists(repo_root: Path) -> bool:
    return all(state_file(repo_root, name).exists() for name in STATE_FILES)


def legacy_workspace_exists(repo_root: Path) -> bool:
    root = workflow_dir(repo_root)
    if not root.exists():
        return False
    return any(workflow_file(repo_root, name).exists() for name in LEGACY_WORKFLOW_FILES)


def workflow_needs_migration(repo_root: Path) -> bool:
    return legacy_workspace_exists(repo_root) and not workflow_exists(repo_root)


@workspace_locked
def load_workspace_state(repo_root: Path) -> dict[str, Any]:
    tasks = read_json(state_file(repo_root, "tasks.json"), default={})
    tasks.setdefault("completed", [])
    tasks.setdefault("in_progress", [])
    tasks.setdefault("next_up", [])
    tasks.setdefault("known_unknowns", [])
    tasks.setdefault("archived", [])
    return {
        "current": read_json(state_file(repo_root, "current.json"), default={}),
        "tasks": tasks,
        "decisions": read_json(state_file(repo_root, "decisions.json"), default={}),
        "sessions": read_json(state_file(repo_root, "sessions.json"), default={}),
        "events": load_events(repo_root),
    }


@workspace_locked
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
            "active_task": state["current"].get("active_task"),
            "task_counts": {
                "completed": len(state["tasks"].get("completed", [])),
                "in_progress": len(state["tasks"].get("in_progress", [])),
                "next_up": len(state["tasks"].get("next_up", [])),
                "archived": len(state["tasks"].get("archived", [])),
                "known_unknowns": len(state["tasks"].get("known_unknowns", [])),
            },
            "session_count": len(state["sessions"].get("items", [])),
            "event_count": len(state.get("events", [])),
            "integrations": state["current"].get("integrations", {}),
        },
    )


@workspace_locked
def render_views(repo_root: Path) -> dict[str, str]:
    state = load_workspace_state(repo_root)
    if _clean_next_slots(state):
        save_workspace_state(repo_root, state)
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
    preserved_next_product_task = current.get("next_product_task") or preserved_next_action
    preserved_workflow_follow_up = current.get("workflow_follow_up") or "无"
    if current.get("packages") and not scan.get("packages") and scan.get("stack") == ["generic"]:
        scan = {**scan}
        for key in ["stack", "framework", "package_manager", "important_files", "source_dirs", "commands", "packages"]:
            scan[key] = current.get(key, scan.get(key))
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
            "packages": scan.get("packages", current.get("packages", [])),
            "tracked_files_count": scan["tracked_files_count"],
            "recent_files": scan["recent_files"],
            "recent_commits": scan["recent_commits"],
            "project_phase": scan["project_phase"],
            "resume_hint": scan["resume_hint"],
            "next_action": preserved_next_action or scan["next_action"],
            "next_product_task": preserved_next_product_task or scan["next_action"],
            "workflow_follow_up": preserved_workflow_follow_up,
            "last_action": action,
            "updated_at": utc_now(),
        }
    )



def _summarize_validation_output(output: str | None, *, max_lines: int = 8, max_chars: int = 1200) -> str:
    clean = (output or "").strip()
    if not clean:
        return "no output"
    lines = clean.splitlines()
    shown = lines[:max_lines]
    summary = "\n".join(shown)
    omitted = len(lines) - len(shown)
    if len(summary) > max_chars:
        summary = summary[:max_chars].rstrip() + "..."
    if omitted > 0:
        summary += f"\n... ({omitted} more lines omitted; full output kept in state/events payload)"
    return summary

def _append_session(state: dict[str, Any], *, title: str, lines: list[str], timestamp: str | None = None) -> None:
    clean_lines = [line for line in lines if line]
    entry = {
        "timestamp": timestamp or utc_now(),
        "title": title,
        "lines": clean_lines,
    }
    items = state["sessions"].setdefault("items", [])
    if items and items[-1].get("title") == title and items[-1].get("lines") == clean_lines:
        items[-1]["timestamp"] = entry["timestamp"]
        return

    # Workspace open is a resume signal, not meaningful task progress. In real
    # agent usage it can be triggered several times around the same handoff and
    # an integration refresh can sit between two otherwise identical resume
    # events. Keep the latest timestamp instead of growing SESSION_LOG noise.
    if title == "workspace open auto-resume":
        for existing in reversed(items):
            if existing.get("title") == title and existing.get("lines") == clean_lines:
                existing["timestamp"] = entry["timestamp"]
                return
            if existing.get("title") in {"start task", "checkpoint", "finish summary"}:
                break

    items.append(entry)



def _extract_line_value(text: str, prefix: str) -> str | None:
    for line in text.splitlines():
        if line.startswith(prefix):
            return line[len(prefix):].strip()
    return None


def _extract_section_value(text: str, heading: str) -> str | None:
    pattern = rf"(?ms)^## {re.escape(heading)}\n(.*?)(?=^## |\Z)"
    match = re.search(pattern, text)
    if not match:
        return None
    for line in match.group(1).splitlines():
        clean = line.strip()
        if clean:
            return clean
    return None


def _latest_finished_next_action(state: dict[str, Any]) -> str | None:
    for event in reversed(state.get("events", [])):
        if event.get("type") != "task_finished":
            continue
        text = str((event.get("payload") or {}).get("next_action") or "").strip()
        if text and not _is_workflow_follow_up_text(text) and not _is_placeholder_next_text(text):
            return text
    return None


def _primary_handoff_next(state: dict[str, Any]) -> str | None:
    current = state.get("current", {})
    completed = _completed_task_texts(state)
    for candidate in (
        _latest_finished_next_action(state),
        current.get("next_product_task"),
        current.get("next_action"),
        _first_pending_product_task(state, exclude_texts=list(completed)),
    ):
        text = str(candidate or "").strip()
        if text and text not in completed and not _is_workflow_follow_up_text(text) and not _is_placeholder_next_text(text):
            return text
    return None


def _prune_workflow_items_from_next_up(state: dict[str, Any], *, keep_text: str | None = None) -> list[str]:
    removed: list[str] = []
    kept: list[dict[str, str]] = []
    keep_lower = (keep_text or "").strip().lower()
    for item in state.get("tasks", {}).get("next_up", []):
        text = (item.get("text") or "").strip()
        if text and _is_workflow_follow_up_text(text) and text.lower() != keep_lower:
            removed.append(text)
            continue
        kept.append(item)
    state.setdefault("tasks", {})["next_up"] = _dedupe_tasks(kept)
    return removed


@state_mutator
def repair_handoff_state(repo_root: Path) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    primary = _primary_handoff_next(state) or "确认下一个具体任务"
    current = state.setdefault("current", {})
    before = {
        "next_action": current.get("next_action"),
        "next_product_task": current.get("next_product_task"),
        "next_up_first": (state.get("tasks", {}).get("next_up") or [{}])[0].get("text"),
    }
    removed = _prune_workflow_items_from_next_up(state, keep_text=primary)
    current["next_action"] = primary
    current["next_product_task"] = primary
    current["updated_at"] = timestamp
    current["last_action"] = "handoff_repaired"
    state.setdefault("tasks", {}).setdefault("next_up", [])
    state["tasks"]["next_up"] = _refresh_next_up(
        state["tasks"].get("next_up", []),
        next_action=primary,
        timestamp=timestamp,
        source="repair-handoff",
        remove_texts=[before.get("next_action"), before.get("next_product_task")],
    )
    _append_session(
        state,
        title="handoff repaired",
        lines=[f"Next action: {primary}", f"Removed workflow backlog items: {', '.join(removed) or 'none'}"],
        timestamp=timestamp,
    )
    save_workspace_state(repo_root, state)
    append_event(repo_root, "handoff_repaired", {"before": before, "next_action": primary, "removed_workflow_backlog": removed})
    render_views(repo_root)
    return {"repo_root": str(repo_root), "next_action": primary, "removed_workflow_backlog": removed, "before": before}


def diagnose_handoff_consistency(repo_root: Path) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    current = state.get("current", {})
    tasks = state.get("tasks", {})
    expected = _primary_handoff_next(state) or "确认下一个具体任务"
    fields: dict[str, str | None] = {
        "current.next_action": current.get("next_action"),
        "current.next_product_task": current.get("next_product_task"),
        "tasks.next_up[0]": (tasks.get("next_up") or [{}])[0].get("text"),
    }
    start_here = view_file(repo_root, "START_HERE.md")
    if start_here.exists():
        text = start_here.read_text(encoding="utf-8")
        fields["START_HERE.Current focus"] = _extract_line_value(text, "- Next action:")
        fields["START_HERE.next_step"] = _extract_line_value(text, "- 下一步：")
    next_action_view = view_file(repo_root, "NEXT_ACTION.md")
    if next_action_view.exists():
        text = next_action_view.read_text(encoding="utf-8")
        fields["NEXT_ACTION.legacy"] = _extract_section_value(text, "Legacy combined next action")
        fields["NEXT_ACTION.product"] = _extract_section_value(text, "Next product task")
    status_view = view_file(repo_root, "STATUS.md")
    if status_view.exists():
        fields["STATUS.next_action"] = _extract_line_value(status_view.read_text(encoding="utf-8"), "- 下一步：")
    mismatches = []
    for name, value in fields.items():
        clean = str(value or "").strip()
        if clean and clean != expected:
            mismatches.append({"field": name, "value": clean, "expected": expected})
    workflow_backlog = [
        (item.get("text") or "").strip()
        for item in tasks.get("next_up", [])
        if (item.get("text") or "").strip() and _is_workflow_follow_up_text((item.get("text") or "").strip())
    ]
    return {
        "expected": expected,
        "fields": fields,
        "mismatches": mismatches,
        "workflow_backlog": workflow_backlog,
        "ok": not mismatches and not workflow_backlog,
    }

@state_mutator
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


@state_mutator
def sync_workspace(repo_root: Path, scan: dict[str, Any], *, action: str, note: str | None = None) -> dict[str, Any]:
    if not workflow_exists(repo_root):
        return bootstrap_workspace(repo_root, scan, action=action, note=note)
    state = load_workspace_state(repo_root)
    current = state["current"]
    previous_next_action = current.get("next_action")
    current["repo_root"] = str(repo_root)
    _touch_current_from_scan(current, scan, action=action)
    _realign_focus_sections(state, timestamp=current["updated_at"], source=action)
    resolved_next_action = current.get("next_action") or scan["next_action"]
    state["tasks"]["next_up"] = _refresh_next_up(
        state["tasks"].get("next_up", []),
        next_action=resolved_next_action,
        timestamp=current["updated_at"],
        source=action,
        remove_texts=[previous_next_action],
    )
    archived_release_items = _archive_stale_release_backlog(state, timestamp=current["updated_at"], source=action)
    lines = [
        f"Stack: {', '.join(scan['stack'])}",
        f"Framework: {', '.join(scan['framework'])}",
        f"Next action: {resolved_next_action}",
    ]
    if archived_release_items:
        lines.append(f"Archived release backlog: {', '.join(archived_release_items)}")
    title = "workspace open auto-resume" if action == "workspace_resumed" else "sync summary"
    if note and note.strip() != title:
        lines.append(f"Note: {note.strip()}")
    _append_session(state, title=title, lines=lines, timestamp=current["updated_at"])
    save_workspace_state(repo_root, state)
    append_event(repo_root, action, {"note": note, "scan": scan})
    render_views(repo_root)
    return state


@state_mutator
def start_task(repo_root: Path, task: str, next_action: str) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    previous_next_action = state["current"].get("next_action")
    state["current"]["active_task"] = task.strip()
    _set_next_slots(state["current"], next_action, prefer_product=True)
    state["current"]["last_action"] = "task_started"
    state["current"]["updated_at"] = timestamp
    state["tasks"]["in_progress"] = _dedupe_tasks([_task_item(task, timestamp=timestamp, source="start"), *state["tasks"].get("in_progress", [])])
    _realign_focus_sections(state, timestamp=timestamp, source="start")
    state["tasks"]["next_up"] = _refresh_next_up(
        state["tasks"].get("next_up", []),
        next_action=next_action.strip(),
        timestamp=timestamp,
        source="start",
        remove_texts=[previous_next_action],
    )
    _append_session(state, title="start task", lines=[f"Task: {task.strip()}", f"Next action: {next_action.strip()}"], timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "task_started", {"task": task.strip(), "next_action": next_action.strip()})
    render_views(repo_root)
    return state


@state_mutator
def record_checkpoint(
    repo_root: Path,
    summary: str,
    next_action: str,
    git_details: dict[str, Any],
    validation: dict[str, Any] | None = None,
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    previous_next_action = state["current"].get("next_action")
    _set_next_slots(state["current"], next_action, prefer_product=False)
    state["current"]["last_action"] = "checkpoint_recorded"
    state["current"]["updated_at"] = timestamp
    _realign_focus_sections(state, timestamp=timestamp, source="checkpoint")
    state["tasks"]["next_up"] = _refresh_next_up(
        state["tasks"].get("next_up", []),
        next_action=next_action.strip(),
        timestamp=timestamp,
        source="checkpoint",
        remove_texts=[previous_next_action],
    )
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
        lines.append(f"validation_output: {_summarize_validation_output(validation.get('output'))}")
        payload["validation"] = validation
    _append_session(state, title="checkpoint", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "checkpoint_recorded", payload)
    render_views(repo_root)
    return state


@state_mutator
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
    previous_next_action = state["current"].get("next_action")
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
    state["current"]["active_task"] = None if matched else state["current"].get("active_task")
    _realign_focus_sections(state, timestamp=timestamp, source="finish")
    excluded_product_texts = [completed_text, matched, state["current"].get("active_task")]
    is_workflow_next = _is_workflow_follow_up_text(next_action)
    product_fallback = _MISSING
    next_up_value = next_action.strip()
    remove_next_texts = [completed_text]
    if is_workflow_next:
        current_product = (state["current"].get("next_product_task") or "").strip()
        if current_product and current_product not in {text for text in excluded_product_texts if text} and not _is_workflow_follow_up_text(current_product):
            product_fallback = current_product
        else:
            product_fallback = _first_pending_product_task(state, exclude_texts=excluded_product_texts)
        if product_fallback is not _MISSING and product_fallback:
            next_up_value = str(product_fallback).strip()
    else:
        remove_next_texts.append(previous_next_action)
    state["tasks"]["next_up"] = _refresh_next_up(
        state["tasks"].get("next_up", []),
        next_action=next_up_value,
        timestamp=timestamp,
        source="finish",
        remove_texts=remove_next_texts,
    )
    _set_next_slots(
        state["current"],
        next_action,
        prefer_product=False,
        product_fallback=product_fallback,
        exclude_product_texts=excluded_product_texts,
    )
    if not is_workflow_next:
        state["current"]["workflow_follow_up"] = "无"
    state["current"]["last_action"] = "task_finished"
    state["current"]["updated_at"] = timestamp
    structured_validation = _structured_validation(validation, timestamp=timestamp)
    if structured_validation:
        state["current"]["last_validation"] = structured_validation
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
        lines.append(f"validation_output: {_summarize_validation_output(validation.get('output'))}")
        payload["validation"] = validation
    _append_session(state, title="finish summary", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "task_finished", payload)
    render_views(repo_root)
    return state, matched


@state_mutator
def record_task_ingress(
    repo_root: Path,
    *,
    source: str,
    task: str,
    next_action: str,
    workspace_action: str,
    context: str | None,
    decision: str | None,
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    clean_source = source.strip() if source and source.strip() else "agent"
    event_name = f"{clean_source}_task_ingressed"
    lines = [
        f"Source: {clean_source}",
        f"Task: {task.strip()}",
        f"Next action: {next_action.strip()}",
        f"Workspace action: {workspace_action}",
    ]
    payload: dict[str, Any] = {
        "source": clean_source,
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
        state["decisions"].setdefault("items", []).append({"timestamp": timestamp, "text": clean_decision, "source": clean_source})
        lines.append(f"Decision: {clean_decision}")
        payload["decision"] = clean_decision
    _append_session(state, title=f"{clean_source} task ingress", lines=lines, timestamp=timestamp)
    state["current"]["updated_at"] = timestamp
    state["current"]["last_action"] = event_name
    save_workspace_state(repo_root, state)
    append_event(repo_root, event_name, payload)
    render_views(repo_root)
    return state


@state_mutator
def record_hermes_ingress(
    repo_root: Path,
    *,
    task: str,
    next_action: str,
    workspace_action: str,
    context: str | None,
    decision: str | None,
) -> dict[str, Any]:
    return record_task_ingress(
        repo_root,
        source="hermes",
        task=task,
        next_action=next_action,
        workspace_action=workspace_action,
        context=context,
        decision=decision,
    )


@state_mutator
def record_integration(
    repo_root: Path,
    *,
    scope: str,
    tools: list[str],
    wrappers: list[str],
    action: str,
    changed_paths: list[str] | None = None,
    skipped_paths: list[str] | None = None,
) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    bucket = state["current"].setdefault("integrations", {}).setdefault(scope, {"tools": [], "wrappers": [], "updated_at": None})
    new_tools = sorted(set(bucket.get("tools", []) + tools))
    new_wrappers = sorted(set(bucket.get("wrappers", []) + wrappers))
    changed_paths = changed_paths or []
    skipped_paths = skipped_paths or []
    unchanged_update = (
        action == "integration_updated"
        and bucket.get("tools", []) == new_tools
        and bucket.get("wrappers", []) == new_wrappers
        and not changed_paths
        and not skipped_paths
    )
    if unchanged_update:
        return state
    bucket["tools"] = new_tools
    bucket["wrappers"] = new_wrappers
    bucket["updated_at"] = timestamp
    state["current"]["updated_at"] = timestamp
    state["current"]["last_action"] = action
    lines = [f"Scope: {scope}", f"Tools: {', '.join(tools)}", f"Wrappers: {', '.join(wrappers) or 'none'}"]
    if changed_paths:
        lines.append(f"Updated files: {', '.join(changed_paths)}")
    if skipped_paths:
        lines.append(f"Skipped read-only integration files: {', '.join(skipped_paths)}")
    _append_session(
        state,
        title="integration installed" if action == "integration_installed" else "integration updated",
        lines=lines,
        timestamp=timestamp,
    )
    save_workspace_state(repo_root, state)
    append_event(repo_root, action, {"scope": scope, "tools": tools, "wrappers": wrappers, "changed_paths": changed_paths, "skipped_paths": skipped_paths})
    render_views(repo_root)
    return state


@state_mutator
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


@state_mutator
def migrate_legacy_workspace(repo_root: Path, scan: dict, *, note: str | None = None) -> dict[str, Any]:
    if workflow_exists(repo_root):
        return sync_workspace(repo_root, scan, action="workspace_migrated", note=note or "state workspace already exists")
    state = _seed_state(repo_root, scan, "workspace_migrated")
    state = _import_legacy_views(repo_root, state)
    timestamp = utc_now()
    lines = [
        "Imported legacy markdown workspace into state.",
        f"Next action: {state['current'].get('next_action', scan['next_action'])}",
    ]
    if note:
        lines.append(f"Note: {note.strip()}")
    _append_session(state, title="legacy workspace migrated", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, "workspace_migrated", {"note": note, "scan": scan})
    render_views(repo_root)
    return state


def workflow_summary(repo_root: Path) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    current = state["current"]
    tasks = state["tasks"]
    integrations = current.get("integrations", {})
    repo_integrations = integrations.get("repo", {})
    user_summary = build_user_summary(state)
    return {
        "repo_root": str(repo_root),
        "repo": current.get("repo_name", repo_root.name),
        "workflow_root": str(workflow_dir(repo_root)),
        "next_action": current.get("next_action"),
        "active_task": current.get("active_task"),
        "last_action": current.get("last_action"),
        "updated_at": current.get("updated_at"),
        "stack": current.get("stack", []),
        "framework": current.get("framework", []),
        "project_phase": current.get("project_phase", "unknown"),
        "resume_hint": current.get("resume_hint", "Confirm the next safe step first."),
        "task_counts": {
            "completed": len(tasks.get("completed", [])),
            "in_progress": len(tasks.get("in_progress", [])),
            "next_up": len(tasks.get("next_up", [])),
            "archived": len(tasks.get("archived", [])),
            "known_unknowns": len(tasks.get("known_unknowns", [])),
        },
        "repo_integrations": repo_integrations,
        "user_summary": user_summary,
        "session_count": len(state["sessions"].get("items", [])),
        "event_count": len(state.get("events", [])),
    }


@state_mutator
def mutate_task_list(
    repo_root: Path,
    *,
    action: str,
    text: str | None = None,
    match: str | None = None,
    section: str = "next_up",
) -> dict[str, Any]:
    valid_sections = {"next_up", "known_unknowns", "in_progress", "completed"}
    if section not in valid_sections:
        raise ValueError(f"Unsupported task section: {section}")
    state = load_workspace_state(repo_root)
    timestamp = utc_now()
    payload: dict[str, Any] = {"action": action, "section": section}
    lines = [f"Action: {action}", f"Section: {section}"]

    if action == "add":
        if not text or not text.strip():
            raise ValueError("task add requires text")
        clean_text = text.strip()
        status = "completed" if section == "completed" else "pending"
        state["tasks"][section] = _dedupe_tasks([_task_item(clean_text, status=status, timestamp=timestamp, source="task"), *state["tasks"].get(section, [])])
        if section == "in_progress":
            state["current"]["active_task"] = clean_text
            _realign_focus_sections(state, timestamp=timestamp, source="task_add")
        payload["text"] = clean_text
        lines.append(f"Task: {clean_text}")
    elif action in {"done", "remove"}:
        if not match or not match.strip():
            raise ValueError(f"task {action} requires match")
        matched_text = None
        search_sections = [section] if action == "remove" else ["in_progress", "next_up", "known_unknowns", section]
        for candidate_section in search_sections:
            updated, matched_text = _remove_task(state["tasks"].get(candidate_section, []), match)
            if matched_text:
                state["tasks"][candidate_section] = updated
                payload["from_section"] = candidate_section
                break
        if not matched_text:
            raise ValueError(f"No task matched: {match}")
        payload["matched"] = matched_text
        lines.append(f"Matched task: {matched_text}")
        if action == "done":
            state["tasks"]["completed"] = _dedupe_tasks([_task_item(matched_text, status="completed", timestamp=timestamp, source="task"), *state["tasks"].get("completed", [])])
        if state["current"].get("active_task") == matched_text:
            state["current"]["active_task"] = None
        _realign_focus_sections(state, timestamp=timestamp, source=f"task_{action}")
    else:
        raise ValueError(f"Unsupported task action: {action}")

    state["current"]["last_action"] = f"task_{action}"
    state["current"]["updated_at"] = timestamp
    _append_session(state, title=f"task {action}", lines=lines, timestamp=timestamp)
    save_workspace_state(repo_root, state)
    append_event(repo_root, f"task_{action}", payload)
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
