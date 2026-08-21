from __future__ import annotations

import json
import multiprocessing
import time
from pathlib import Path

import pytest

from autorunne.core.persistence import (
    StateCorruptionError,
    StateLockTimeoutError,
    atomic_write_json,
    atomic_write_jsonl,
    read_json_recovering,
    read_jsonl_recovering,
    workspace_lock,
)


def _hold_lock(repo: str, ready: multiprocessing.Event) -> None:
    with workspace_lock(Path(repo), timeout=2.0):
        ready.set()
        time.sleep(0.8)


def test_atomic_json_keeps_last_known_good_backup(tmp_path: Path):
    target = tmp_path / ".autorunne" / "state" / "sessions.json"
    atomic_write_json(target, {"items": [{"title": "first"}]})
    atomic_write_json(target, {"items": [{"title": "second"}]})
    assert json.loads(target.read_text())["items"][0]["title"] == "second"
    backup = target.with_name("sessions.json.bak")
    assert json.loads(backup.read_text())["items"][0]["title"] == "first"


def test_malformed_primary_recovers_from_valid_backup(tmp_path: Path):
    target = tmp_path / ".autorunne" / "state" / "sessions.json"
    atomic_write_json(target, {"items": [{"title": "first"}]})
    atomic_write_json(target, {"items": [{"title": "second"}]})
    target.write_text("{", encoding="utf-8")
    recovered = read_json_recovering(target, default={})
    assert recovered == {"items": [{"title": "first"}]}
    assert json.loads(target.read_text()) == recovered


def test_malformed_primary_and_backup_fail_closed(tmp_path: Path):
    target = tmp_path / ".autorunne" / "state" / "sessions.json"
    target.parent.mkdir(parents=True)
    target.write_text("{", encoding="utf-8")
    target.with_name("sessions.json.bak").write_text("[", encoding="utf-8")
    with pytest.raises(StateCorruptionError, match="sessions.json"):
        read_json_recovering(target, default={})
    assert target.read_text() == "{"
    assert target.with_name("sessions.json.bak").read_text() == "["


def test_workspace_lock_times_out_while_other_process_holds_it(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    ready = multiprocessing.Event()
    process = multiprocessing.Process(target=_hold_lock, args=(str(repo), ready))
    process.start()
    assert ready.wait(timeout=2.0)
    try:
        with pytest.raises(StateLockTimeoutError, match="retry"):
            with workspace_lock(repo, timeout=0.1, poll_interval=0.01):
                pass
    finally:
        process.join(timeout=2.0)
        if process.is_alive():
            process.terminate()


def test_jsonl_repairs_only_an_incomplete_final_line(tmp_path: Path):
    target = tmp_path / ".autorunne/state/events.jsonl"
    target.parent.mkdir(parents=True)
    target.write_text(
        '{"type":"first"}\n{"type":"second"', encoding="utf-8"
    )
    assert read_jsonl_recovering(target) == [{"type": "first"}]
    assert target.read_text(encoding="utf-8") == '{"type": "first"}\n'


def test_jsonl_middle_corruption_fails_closed(tmp_path: Path):
    target = tmp_path / ".autorunne/state/events.jsonl"
    target.parent.mkdir(parents=True)
    original = '{"type":"first"}\n{bad}\n{"type":"third"}\n'
    target.write_text(original, encoding="utf-8")
    with pytest.raises(StateCorruptionError, match="before the final line"):
        read_jsonl_recovering(target)
    assert target.read_text(encoding="utf-8") == original


def test_workspace_lock_is_reentrant_in_one_thread(tmp_path: Path):
    repo = tmp_path / "repo"
    repo.mkdir()
    with workspace_lock(repo, timeout=0.1):
        with workspace_lock(repo, timeout=0.1):
            atomic_write_json(
                repo / ".autorunne/state/current.json", {"ok": True}
            )


def test_failed_primary_replace_leaves_previous_json_complete(
    tmp_path: Path, monkeypatch
):
    import autorunne.core.persistence as persistence

    target = tmp_path / ".autorunne/state/current.json"
    atomic_write_json(target, {"generation": "old"})
    original_replace = persistence.os.replace

    def fail_primary_replace(source, destination):
        if Path(destination) == target:
            raise OSError("simulated interrupted replace")
        return original_replace(source, destination)

    monkeypatch.setattr(persistence.os, "replace", fail_primary_replace)
    with pytest.raises(OSError, match="interrupted replace"):
        atomic_write_json(target, {"generation": "new"})
    assert json.loads(target.read_text()) == {"generation": "old"}
    assert list(target.parent.glob(f".{target.name}.*.tmp")) == []
