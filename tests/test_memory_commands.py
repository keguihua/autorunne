from __future__ import annotations

import json
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autorunne.cli import app

runner = CliRunner()


def _run_in(repo: Path, args: list[str]):
    old = Path.cwd()
    try:
        import os

        os.chdir(repo)
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old)


def _append_session(repo: Path, idx: int, month: str = "2026-01") -> None:
    path = repo / ".autorunne" / "state" / "sessions.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.setdefault("items", []).append(
        {
            "timestamp": f"{month}-{(idx % 28) + 1:02d} 09:00 UTC",
            "title": f"test session {idx}",
            "lines": [f"Summary: session {idx}", f"Next action: task {idx}"],
        }
    )
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _append_event(repo: Path, idx: int, month: str = "2026-01") -> None:
    path = repo / ".autorunne" / "state" / "events.jsonl"
    event = {
        "timestamp": f"{month}-{(idx % 28) + 1:02d} 09:00 UTC",
        "type": "test_event",
        "payload": {"summary": f"event {idx}"},
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(event, ensure_ascii=False) + "\n")


def _update_config(repo: Path, **updates) -> None:
    path = repo / ".autorunne" / "config.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    data.update(updates)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def test_memory_report_recommends_compaction_when_records_exceed_window(python_repo: Path):
    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    result = _run_in(python_repo, ["memory-report", "--keep-sessions", "3"])

    assert result.exit_code == 0
    assert "Autorunne Memory Report" in result.stdout
    assert "run `autorunne compact --dry-run --keep-sessions 3`" in result.stdout


def test_compact_dry_run_does_not_modify_state(python_repo: Path):
    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)
    sessions_before = (python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8")
    events_before = (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8")

    result = _run_in(python_repo, ["compact", "--keep-sessions", "3", "--dry-run"])

    assert result.exit_code == 0
    assert "Compact preview" in result.stdout
    assert "archived" in result.stdout
    assert sessions_before == (python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8")
    assert events_before == (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8")
    assert not (python_repo / ".autorunne" / "archive" / "2026-01.md").exists()


def test_compact_archives_old_records_and_writes_summary(python_repo: Path):
    _run_in(python_repo, ["open"])
    for idx in range(8):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    result = _run_in(python_repo, ["compact", "--keep-sessions", "3"])

    assert result.exit_code == 0
    assert "Compacted Autorunne memory" in result.stdout
    archive = python_repo / ".autorunne" / "archive" / "2026-01.md"
    assert archive.exists()
    assert "test session 0" in archive.read_text(encoding="utf-8")
    summary = python_repo / ".autorunne" / "SUMMARY.md"
    assert summary.exists()
    assert "Project Memory Summary" in summary.read_text(encoding="utf-8")
    sessions = json.loads((python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8"))["items"]
    assert len(sessions) == 4  # 3 recent + compaction session
    assert sessions[-1]["title"] == "memory compacted"
    events = (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(events) == 4  # 3 recent + compaction event
    assert "memory_compacted" in events[-1]


def test_export_session_writes_shareable_markdown(python_repo: Path):
    _run_in(python_repo, ["open"])
    for idx in range(4):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    result = _run_in(python_repo, ["export-session", "--last", "2"])

    assert result.exit_code == 0
    assert "Session export:" in result.stdout
    exports = sorted((python_repo / ".autorunne" / "exports").glob("session-*.md"))
    assert exports
    text = exports[-1].read_text(encoding="utf-8")
    assert "Autorunne Session Export" in text
    assert "test session 3" in text
    assert "event 3" in text


def test_auto_compact_runs_after_common_write_when_threshold_is_exceeded(python_repo: Path):
    _run_in(python_repo, ["open"])
    _update_config(
        python_repo,
        auto_compact_enabled=True,
        auto_compact_threshold=5,
        auto_compact_keep_sessions=3,
    )
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    result = _run_in(python_repo, ["start", "--task", "trigger auto compact"])

    assert result.exit_code == 0
    assert (python_repo / ".autorunne" / "archive" / "2026-01.md").exists()
    assert (python_repo / ".autorunne" / "SUMMARY.md").exists()
    sessions = json.loads((python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8"))["items"]
    assert len(sessions) == 4  # 3 recent + compaction session
    assert sessions[-1]["title"] == "memory compacted"
    events = (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8").splitlines()
    assert len(events) == 4  # 3 recent + compaction event
    assert "memory_compacted" in events[-1]


def test_auto_compact_can_be_disabled_in_config(python_repo: Path):
    _run_in(python_repo, ["open"])
    _update_config(
        python_repo,
        auto_compact_enabled=False,
        auto_compact_threshold=5,
        auto_compact_keep_sessions=3,
    )
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    result = _run_in(python_repo, ["start", "--task", "do not auto compact"])

    assert result.exit_code == 0
    assert not (python_repo / ".autorunne" / "archive" / "2026-01.md").exists()
    sessions = json.loads((python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8"))["items"]
    assert len(sessions) > 5


def test_two_same_month_compactions_preserve_both_batches(python_repo: Path):
    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    first = _run_in(python_repo, ["compact", "--keep-sessions", "3"])
    assert first.exit_code == 0
    archive_path = python_repo / ".autorunne" / "archive" / "2026-01.md"
    first_archive = archive_path.read_text(encoding="utf-8")
    assert "test session 0" in first_archive

    for idx in range(6, 12):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    second = _run_in(python_repo, ["compact", "--keep-sessions", "3"])
    assert second.exit_code == 0
    archive = archive_path.read_text(encoding="utf-8")
    assert "test session 0" in archive
    assert "test session 6" in archive
    assert archive.count("<!-- autorunne-archive-batch:") == 2


def test_archive_batch_write_is_idempotent(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    original_save = memory.save_workspace_state
    calls = {"count": 0}

    def fail_once(repo_root, state):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated crash after archive persistence")
        return original_save(repo_root, state)

    monkeypatch.setattr(memory, "save_workspace_state", fail_once)
    with pytest.raises(RuntimeError, match="simulated crash after archive persistence"):
        memory.compact_memory(python_repo, keep_sessions=3)

    monkeypatch.setattr(memory, "save_workspace_state", original_save)
    memory.compact_memory(python_repo, keep_sessions=3)

    archive = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    assert archive.count("<!-- autorunne-archive-batch:") == 1
    assert archive.count("test session 0") == 1
    assert archive.count("event 0") == 1


def test_compact_retry_after_event_rewrite_crash_is_idempotent(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    original_write = memory._write_events
    calls = {"count": 0}

    def fail_once(repo_root, events):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated crash after session save")
        return original_write(repo_root, events)

    monkeypatch.setattr(memory, "_write_events", fail_once)
    with pytest.raises(RuntimeError, match="simulated crash after session save"):
        memory.compact_memory(python_repo, keep_sessions=3)

    monkeypatch.setattr(memory, "_write_events", original_write)
    memory.compact_memory(python_repo, keep_sessions=3)

    archive = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    assert archive.count("<!-- autorunne-archive-batch:") == 1
    assert archive.count("test session 0") == 1
    assert archive.count("event 0") == 1
    assert archive.count("event 1") == 1


def test_compact_after_crash_retry_still_appends_a_new_batch(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    original_write = memory._write_events
    calls = {"count": 0}

    def fail_once(repo_root, events):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated crash after session save")
        return original_write(repo_root, events)

    monkeypatch.setattr(memory, "_write_events", fail_once)
    with pytest.raises(RuntimeError, match="simulated crash after session save"):
        memory.compact_memory(python_repo, keep_sessions=3)
    monkeypatch.setattr(memory, "_write_events", original_write)
    memory.compact_memory(python_repo, keep_sessions=3)

    for idx in range(6, 12):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)
    memory.compact_memory(python_repo, keep_sessions=3)

    archive = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    assert archive.count("<!-- autorunne-archive-batch:") == 2
    assert archive.count("test session 0") == 1
    assert archive.count("test session 6") == 1
    assert archive.count("event 0") == 1
    assert archive.count("event 6") == 1


def _pending_path(repo: Path) -> Path:
    return repo / ".autorunne" / "runtime" / "pending-compaction.json"


def _crash_compact_after_session_save(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _run_in(python_repo, ["open"])
    for idx in range(6):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)

    original_write = memory._write_events
    calls = {"count": 0}

    def fail_once(repo_root, events):
        calls["count"] += 1
        if calls["count"] == 1:
            raise RuntimeError("simulated crash after session save")
        return original_write(repo_root, events)

    monkeypatch.setattr(memory, "_write_events", fail_once)
    with pytest.raises(RuntimeError, match="simulated crash after session save"):
        memory.compact_memory(python_repo, keep_sessions=3)
    monkeypatch.setattr(memory, "_write_events", original_write)
    assert _pending_path(python_repo).exists()
    return original_write


def test_pending_compaction_recovers_before_new_manual_record(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _crash_compact_after_session_save(python_repo, monkeypatch)
    result = _run_in(
        python_repo,
        [
            "record",
            "--summary",
            "record created after crash",
            "--next",
            "continue after crash",
        ],
    )
    assert result.exit_code == 0
    if _pending_path(python_repo).exists():
        memory.compact_memory(python_repo, keep_sessions=3)

    sessions_text = (python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8")
    events_text = (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8")
    current = json.loads((python_repo / ".autorunne" / "state" / "current.json").read_text(encoding="utf-8"))
    archive = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    assert sessions_text.count("record created after crash") == 1
    assert events_text.count("record created after crash") == 1
    assert archive.count("<!-- autorunne-archive-batch:") == 1
    assert archive.count("test session 0") == 1
    assert archive.count("event 0") == 1
    assert not _pending_path(python_repo).exists()
    assert current["next_action"] == "continue after crash"


def test_pending_compaction_recovers_before_new_start(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _crash_compact_after_session_save(python_repo, monkeypatch)
    result = _run_in(
        python_repo,
        ["start", "--task", "task after crash", "--next", "next after crash"],
    )
    assert result.exit_code == 0
    if _pending_path(python_repo).exists():
        memory.compact_memory(python_repo, keep_sessions=3)

    sessions_text = (python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8")
    events_text = (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8")
    current = json.loads((python_repo / ".autorunne" / "state" / "current.json").read_text(encoding="utf-8"))
    archive = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    assert sessions_text.count("task after crash") == 1
    assert events_text.count("task after crash") == 1
    assert current["active_task"] == "task after crash"
    assert current["next_action"] == "next after crash"
    assert archive.count("<!-- autorunne-archive-batch:") == 1
    assert not _pending_path(python_repo).exists()


def test_failed_pending_recovery_blocks_new_state_mutation(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _crash_compact_after_session_save(python_repo, monkeypatch)
    sessions_before = (python_repo / ".autorunne" / "state" / "sessions.json").read_bytes()
    events_before = (python_repo / ".autorunne" / "state" / "events.jsonl").read_bytes()
    current_before = (python_repo / ".autorunne" / "state" / "current.json").read_bytes()
    tasks_before = (python_repo / ".autorunne" / "state" / "tasks.json").read_bytes()

    def fail_recovery(repo_root, events):
        raise RuntimeError("simulated pending recovery failure")

    monkeypatch.setattr(memory, "_write_events", fail_recovery)
    result = _run_in(
        python_repo,
        [
            "record",
            "--summary",
            "record created after crash",
            "--next",
            "continue after crash",
        ],
    )
    combined = f"{result.stdout}{result.stderr}"
    assert result.exit_code == 1
    assert "compact" in combined.lower()
    assert "record created after crash" not in (
        python_repo / ".autorunne" / "state" / "sessions.json"
    ).read_text(encoding="utf-8")
    assert "record created after crash" not in (
        python_repo / ".autorunne" / "state" / "events.jsonl"
    ).read_text(encoding="utf-8")
    assert _pending_path(python_repo).exists()
    assert (python_repo / ".autorunne" / "state" / "events.jsonl").read_bytes() == events_before
    assert (python_repo / ".autorunne" / "state" / "current.json").read_bytes() == current_before
    assert (python_repo / ".autorunne" / "state" / "tasks.json").read_bytes() == tasks_before
    assert "continue after crash" not in (python_repo / ".autorunne" / "state" / "current.json").read_text(
        encoding="utf-8"
    )
    assert sessions_before  # crash left a sessions file; mutation must not add the new record


def test_pending_recovery_then_new_compact_appends_one_batch(python_repo: Path, monkeypatch):
    from autorunne.core import memory

    _crash_compact_after_session_save(python_repo, monkeypatch)
    recorded = _run_in(
        python_repo,
        [
            "record",
            "--summary",
            "record created after crash",
            "--next",
            "continue after crash",
        ],
    )
    assert recorded.exit_code == 0
    if _pending_path(python_repo).exists():
        memory.compact_memory(python_repo, keep_sessions=3)

    for idx in range(6, 12):
        _append_session(python_repo, idx)
        _append_event(python_repo, idx)
    compacted = _run_in(python_repo, ["compact", "--keep-sessions", "3"])
    assert compacted.exit_code == 0

    january = (python_repo / ".autorunne" / "archive" / "2026-01.md").read_text(encoding="utf-8")
    archives = "".join(
        path.read_text(encoding="utf-8")
        for path in sorted((python_repo / ".autorunne" / "archive").glob("*.md"))
    )
    live = (python_repo / ".autorunne" / "state" / "sessions.json").read_text(
        encoding="utf-8"
    ) + (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8")
    assert january.count("<!-- autorunne-archive-batch:") == 2
    assert january.count("test session 0") == 1
    assert january.count("test session 6") == 1
    assert january.count("event 0") == 1
    assert "record created after crash" in archives + live
    assert not _pending_path(python_repo).exists()
