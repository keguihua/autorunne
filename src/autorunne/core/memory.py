from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from autorunne.core.paths import ensure_dir, load_config, state_file, workflow_dir, workflow_file
from autorunne.core.persistence import atomic_write_jsonl, atomic_write_text, workspace_locked
from autorunne.core.state_engine import append_event, load_events, load_workspace_state, render_views, save_workspace_state, utc_now


def _parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    clean = value.strip()
    for fmt in ("%Y-%m-%d %H:%M UTC", "%Y-%m-%d"):
        try:
            parsed = datetime.strptime(clean[: len(datetime.now().strftime(fmt))], fmt)
            return parsed.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
    try:
        return datetime.fromisoformat(clean.replace("Z", "+00:00"))
    except ValueError:
        return None


def _month_key(timestamp: str | None) -> str:
    parsed = _parse_timestamp(timestamp)
    if parsed:
        return parsed.strftime("%Y-%m")
    return "unknown"


def _session_bullet(item: dict[str, Any]) -> str:
    title = str(item.get("title") or "session").strip()
    lines = [str(line).strip() for line in item.get("lines", []) if str(line).strip()]
    first = lines[0] if lines else "No details recorded"
    timestamp = str(item.get("timestamp") or "unknown").strip()
    return f"- {timestamp} | {title}: {first}"


def _event_bullet(item: dict[str, Any]) -> str:
    timestamp = str(item.get("timestamp") or "unknown").strip()
    event_type = str(item.get("type") or "event").strip()
    payload = item.get("payload") or {}
    summary = payload.get("summary") or payload.get("task") or payload.get("next_action") or payload.get("note") or "recorded"
    return f"- {timestamp} | {event_type}: {str(summary).strip()}"


def _human_size(size: int) -> str:
    value = float(size)
    for unit in ("B", "KB", "MB", "GB"):
        if value < 1024 or unit == "GB":
            return f"{value:.1f} {unit}" if unit != "B" else f"{int(value)} B"
        value /= 1024
    return f"{size} B"


def _archive_batch_id(
    sessions: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> str:
    canonical = json.dumps(
        {"sessions": sessions, "events": events},
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _merge_archive_batch(
    archive_path: Path,
    *,
    month: str,
    batch_id: str,
    timestamp: str,
    sessions: list[dict[str, Any]],
    events: list[dict[str, Any]],
) -> bool:
    marker = f"<!-- autorunne-archive-batch:{batch_id} -->"
    existing = (
        archive_path.read_text(encoding="utf-8")
        if archive_path.exists()
        else f"# Autorunne Archive - {month}\n"
    )
    if marker in existing:
        return False
    section_lines = [
        marker,
        f"## Compaction batch — {timestamp}",
        "",
        "### Session summary",
        "",
    ]
    session_bullets = [_session_bullet(item) for item in sessions]
    section_lines.extend(session_bullets or ["- none"])
    section_lines.extend(["", "### Event summary", ""])
    event_bullets = [_event_bullet(item) for item in events]
    section_lines.extend(event_bullets or ["- none"])
    section = "\n".join(section_lines).rstrip() + "\n"
    atomic_write_text(archive_path, existing.rstrip() + "\n\n" + section)
    return True


def _write_events(repo_root: Path, events: list[dict[str, Any]]) -> None:
    atomic_write_jsonl(state_file(repo_root, "events.jsonl"), events)


def build_memory_summary(state: dict[str, Any]) -> str:
    current = state.get("current", {})
    tasks = state.get("tasks", {})
    decisions = state.get("decisions", {})
    last_validation = current.get("last_validation") or {}
    completed = tasks.get("completed", [])[-10:]
    next_up = tasks.get("next_up", [])[:5]
    decision_items = decisions.get("items", [])[-20:]
    lines = [
        "# Project Memory Summary",
        "",
        "This file is a compact long-term memory layer. Detailed recent records stay in `SESSION_LOG.md`; older history can be archived under `.autorunne/archive/`.",
        "",
        "## Current state",
        f"- Project: {current.get('repo_name', 'unknown')}",
        f"- Last action: {current.get('last_action', 'unknown')}",
        f"- Active task: {current.get('active_task') or 'none'}",
        f"- Next action: {current.get('next_action') or 'Confirm the next concrete step.'}",
        f"- Last validation: {last_validation.get('status', 'not recorded')} ({last_validation.get('command', 'no command')})",
        "",
        "## Recent completed tasks",
    ]
    lines.extend(f"- {item.get('timestamp', 'unknown')}: {item.get('text', '').strip()}" for item in completed if item.get("text"))
    if len(lines) and lines[-1] == "## Recent completed tasks":
        lines.append("- none recorded yet")
    lines.append("")
    lines.append("## Next product backlog")
    backlog_lines = [f"- {item.get('text', '').strip()}" for item in next_up if item.get("text")]
    lines.extend(backlog_lines or ["- none recorded yet"])
    lines.append("")
    lines.append("## Durable decisions")
    lines.extend(f"- {item.get('timestamp', 'unknown')}: {item.get('text', '').strip()}" for item in decision_items if item.get("text"))
    if lines[-1] == "## Durable decisions":
        lines.append("- none recorded yet")
    lines.append("")
    lines.append("## Long-term memory policy")
    lines.append("- Keep the current handoff files short: START_HERE, STATUS, NEXT_ACTION.")
    lines.append("- Keep about 100-200 recent detailed records for agent context; default compact window is 200.")
    lines.append("- Summarize and archive older sessions/events instead of deleting project history outright.")
    return "\n".join(lines).rstrip() + "\n"


def memory_report(repo_root: Path, *, keep_sessions: int = 200) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    root = workflow_dir(repo_root)
    files: list[dict[str, Any]] = []
    total = 0
    if root.exists():
        for path in root.rglob("*"):
            if path.is_file():
                size = path.stat().st_size
                total += size
                files.append({"path": str(path.relative_to(root)), "size": size, "human_size": _human_size(size)})
    files.sort(key=lambda item: item["size"], reverse=True)
    session_count = len(state.get("sessions", {}).get("items", []))
    event_count = len(load_events(repo_root))
    recommendation = "no compaction needed"
    if session_count > keep_sessions or event_count > keep_sessions:
        recommendation = f"run `autorunne compact --dry-run --keep-sessions {keep_sessions}`"
    return {
        "workflow_root": str(root),
        "total_size": total,
        "human_total_size": _human_size(total),
        "session_count": session_count,
        "event_count": event_count,
        "keep_sessions": keep_sessions,
        "recommendation": recommendation,
        "largest_files": files[:10],
    }


def export_session(repo_root: Path, *, last: int = 20, since: str | None = None, output: str | None = None) -> dict[str, Any]:
    state = load_workspace_state(repo_root)
    sessions = list(state.get("sessions", {}).get("items", []))
    events = load_events(repo_root)
    since_dt = _parse_timestamp(since) if since else None
    if since_dt:
        sessions = [item for item in sessions if (_parse_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_dt]
        events = [item for item in events if (_parse_timestamp(item.get("timestamp")) or datetime.min.replace(tzinfo=timezone.utc)) >= since_dt]
    else:
        sessions = sessions[-last:]
        events = events[-last:]
    current = state.get("current", {})
    exports_dir = ensure_dir(workflow_dir(repo_root) / "exports")
    date_token = datetime.now(timezone.utc).strftime("%Y-%m-%d-%H%M")
    out_path = Path(output).expanduser().resolve() if output else exports_dir / f"session-{date_token}.md"
    ensure_dir(out_path.parent)
    lines = [
        f"# Autorunne Session Export - {current.get('repo_name', repo_root.name)}",
        "",
        f"Generated at: {utc_now()}",
        f"Scope: {'since ' + since if since else 'last ' + str(last)}",
        "",
        "## Current handoff",
        f"- Last action: {current.get('last_action', 'unknown')}",
        f"- Active task: {current.get('active_task') or 'none'}",
        f"- Next action: {current.get('next_action') or 'Confirm the next concrete step.'}",
        "",
        "## Sessions",
    ]
    lines.extend(_session_bullet(item) for item in sessions)
    if not sessions:
        lines.append("- none")
    lines.extend(["", "## Events"])
    lines.extend(_event_bullet(item) for item in events)
    if not events:
        lines.append("- none")
    out_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return {"path": str(out_path), "sessions": len(sessions), "events": len(events)}


@workspace_locked
def compact_memory(repo_root: Path, *, keep_sessions: int = 200, dry_run: bool = False) -> dict[str, Any]:
    if keep_sessions < 1:
        raise ValueError("keep_sessions must be at least 1")
    state = load_workspace_state(repo_root)
    sessions = list(state.get("sessions", {}).get("items", []))
    events = load_events(repo_root)
    old_sessions = sessions[:-keep_sessions] if len(sessions) > keep_sessions else []
    kept_sessions = sessions[-keep_sessions:] if len(sessions) > keep_sessions else sessions
    old_events = events[:-keep_sessions] if len(events) > keep_sessions else []
    kept_events = events[-keep_sessions:] if len(events) > keep_sessions else events
    archive_counts: dict[str, dict[str, int]] = defaultdict(lambda: {"sessions": 0, "events": 0})
    for item in old_sessions:
        archive_counts[_month_key(item.get("timestamp"))]["sessions"] += 1
    for item in old_events:
        archive_counts[_month_key(item.get("timestamp"))]["events"] += 1
    summary_text = build_memory_summary(state)
    archive_files = [str(workflow_dir(repo_root) / "archive" / f"{month}.md") for month in sorted(archive_counts)]
    result = {
        "repo_root": str(repo_root),
        "dry_run": dry_run,
        "keep_sessions": keep_sessions,
        "sessions_before": len(sessions),
        "sessions_after": len(kept_sessions) + (0 if dry_run or not old_sessions else 1),
        "events_before": len(events),
        "events_after": len(kept_events) + (0 if dry_run or not (old_sessions or old_events) else 1),
        "archived_sessions": len(old_sessions),
        "archived_events": len(old_events),
        "archive_files": archive_files,
        "summary_path": str(workflow_file(repo_root, "SUMMARY.md")),
    }
    if dry_run:
        return result

    archive_dir = ensure_dir(workflow_dir(repo_root) / "archive")
    grouped_sessions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    grouped_events: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for item in old_sessions:
        grouped_sessions[_month_key(item.get("timestamp"))].append(item)
    for item in old_events:
        grouped_events[_month_key(item.get("timestamp"))].append(item)
    timestamp = utc_now()
    for month in sorted(set(grouped_sessions) | set(grouped_events)):
        month_sessions = grouped_sessions.get(month, [])
        month_events = grouped_events.get(month, [])
        _merge_archive_batch(
            archive_dir / f"{month}.md",
            month=month,
            batch_id=_archive_batch_id(month_sessions, month_events),
            timestamp=timestamp,
            sessions=month_sessions,
            events=month_events,
        )

    state.setdefault("sessions", {})["items"] = kept_sessions
    if old_sessions or old_events:
        state["sessions"]["items"].append(
            {
                "timestamp": timestamp,
                "title": "memory compacted",
                "lines": [
                    f"Kept recent detailed records: {keep_sessions}",
                    f"Archived sessions: {len(old_sessions)}",
                    f"Archived events: {len(old_events)}",
                    f"Archive files: {', '.join(archive_files) or 'none'}",
                ],
            }
        )
        state.setdefault("current", {})["last_action"] = "memory_compacted"
        state.setdefault("current", {})["updated_at"] = timestamp
    save_workspace_state(repo_root, state)
    _write_events(repo_root, kept_events)
    if old_sessions or old_events:
        append_event(repo_root, "memory_compacted", {k: v for k, v in result.items() if k != "dry_run"})
    atomic_write_text(workflow_file(repo_root, "SUMMARY.md"), summary_text)
    render_views(repo_root)
    return result


def maybe_auto_compact(repo_root: Path, *, reason: str = "command") -> dict[str, Any]:
    """Run safe automatic compaction when repo-local memory grows past config limits.

    Defaults are intentionally conservative: auto compaction only starts after
    1000 detailed session/event records, and keeps the most recent 200 records.
    Older records are archived, not deleted.
    """
    config = load_config(repo_root)
    enabled = bool(getattr(config, "auto_compact_enabled", True))
    threshold = int(getattr(config, "auto_compact_threshold", 1000) or 0)
    keep_sessions = int(getattr(config, "auto_compact_keep_sessions", 200) or 200)
    state = load_workspace_state(repo_root)
    session_count = len(state.get("sessions", {}).get("items", []))
    event_count = len(load_events(repo_root))
    result: dict[str, Any] = {
        "auto_compact": False,
        "enabled": enabled,
        "threshold": threshold,
        "keep_sessions": keep_sessions,
        "session_count": session_count,
        "event_count": event_count,
        "reason": reason,
    }
    if not enabled:
        result["skipped"] = "disabled"
        return result
    if threshold < 1:
        result["skipped"] = "threshold_disabled"
        return result
    if keep_sessions < 1:
        keep_sessions = 200
        result["keep_sessions"] = keep_sessions
    if max(session_count, event_count) <= threshold:
        result["skipped"] = "below_threshold"
        return result
    compacted = compact_memory(repo_root, keep_sessions=keep_sessions, dry_run=False)
    compacted.update({"auto_compact": True, "threshold": threshold, "reason": reason})
    return compacted
