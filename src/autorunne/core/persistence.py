from __future__ import annotations

import json
import os
import tempfile
import threading
import time
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

F = TypeVar("F", bound=Callable[..., Any])


class StateCorruptionError(RuntimeError):
    pass


class StateLockTimeoutError(RuntimeError):
    pass


class _LockState:
    def __init__(self) -> None:
        self.gate = threading.RLock()
        self.depth = 0
        self.handle: Any = None


_LOCKS: dict[str, _LockState] = {}
_LOCKS_GUARD = threading.Lock()


def _lock_state(repo_root: Path) -> _LockState:
    key = str(repo_root.resolve())
    with _LOCKS_GUARD:
        state = _LOCKS.get(key)
        if state is None:
            state = _LockState()
            _LOCKS[key] = state
        return state


def _try_os_lock(handle: Any) -> bool:
    if os.name == "nt":
        import msvcrt

        try:
            handle.seek(0, os.SEEK_END)
            if handle.tell() == 0:
                handle.write(b"\0")
                handle.flush()
            handle.seek(0)
            msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            return True
        except OSError:
            return False
    import fcntl

    try:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        return True
    except OSError:
        return False


def _unlock_os(handle: Any) -> None:
    if os.name == "nt":
        import msvcrt

        handle.seek(0)
        msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
        return
    import fcntl

    fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def _fsync_directory(directory: Path) -> None:
    if os.name == "nt":
        return
    descriptor = os.open(directory, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _corruption_message(path: Path, detail: str) -> str:
    backup = path.with_name(path.name + ".bak")
    return (
        f"Autorunne state is corrupt and did not reset state. {detail} "
        f"Primary: {path}. Backup: {backup}. "
        "Preserve .autorunne/, inspect the files, or restore from your own backup. "
        "Autorunne did not reset state."
    )


@contextmanager
def workspace_lock(
    repo_root: Path,
    *,
    timeout: float = 10.0,
    poll_interval: float = 0.05,
) -> Iterator[None]:
    state = _lock_state(repo_root)
    state.gate.acquire()
    try:
        if state.depth == 0:
            path = repo_root / ".autorunne/runtime/state.lock"
            path.parent.mkdir(parents=True, exist_ok=True)
            handle = path.open("a+b")
            deadline = time.monotonic() + timeout
            while not _try_os_lock(handle):
                if time.monotonic() >= deadline:
                    handle.close()
                    raise StateLockTimeoutError(
                        f"Autorunne state is busy for {repo_root}. "
                        "Wait for the other command to finish, then retry."
                    )
                time.sleep(poll_interval)
            state.handle = handle
        state.depth += 1
        try:
            yield
        finally:
            state.depth -= 1
            if state.depth == 0 and state.handle is not None:
                _unlock_os(state.handle)
                state.handle.close()
                state.handle = None
    finally:
        state.gate.release()


def workspace_locked(function: F) -> F:
    @wraps(function)
    def wrapped(repo_root: Path, *args: Any, **kwargs: Any):
        with workspace_lock(repo_root):
            return function(repo_root, *args, **kwargs)

    return wrapped  # type: ignore[return-value]


def _atomic_replace_bytes(path: Path, content: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor, temp_name = tempfile.mkstemp(
        prefix=f".{path.name}.",
        suffix=".tmp",
        dir=path.parent,
    )
    temp_path = Path(temp_name)
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(content)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, path)
        _fsync_directory(path.parent)
    finally:
        if temp_path.exists():
            temp_path.unlink()


def atomic_write_text(path: Path, content: str) -> None:
    _atomic_replace_bytes(path, content.encode("utf-8"))


def atomic_write_json(path: Path, payload: Any) -> None:
    serialized = json.dumps(payload, indent=2, ensure_ascii=False) + "\n"
    if path.exists():
        current = path.read_bytes()
        try:
            json.loads(current.decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            pass
        else:
            _atomic_replace_bytes(path.with_name(path.name + ".bak"), current)
    _atomic_replace_bytes(path, serialized.encode("utf-8"))


def read_json_recovering(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError):
        pass
    backup = path.with_name(path.name + ".bak")
    if backup.exists():
        try:
            recovered = json.loads(backup.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError):
            recovered = None
        else:
            _atomic_replace_bytes(path, backup.read_bytes())
            return recovered
    raise StateCorruptionError(
        _corruption_message(path, f"Unrecoverable JSON in {path.name}.")
    )


def _parse_jsonl(
    text: str,
    path: Path,
    *,
    allow_tail_repair: bool,
) -> tuple[list[dict[str, Any]], bool]:
    events: list[dict[str, Any]] = []
    repaired_tail = False
    lines = text.splitlines()
    last_index = len(lines) - 1
    for index, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        try:
            parsed = json.loads(stripped)
        except json.JSONDecodeError:
            is_final_line = index == last_index
            if allow_tail_repair and is_final_line:
                repaired_tail = True
                break
            if not is_final_line:
                raise StateCorruptionError(
                    _corruption_message(
                        path,
                        f"Malformed JSONL before the final line in {path.name}.",
                    )
                ) from None
            raise StateCorruptionError(
                _corruption_message(path, f"Unrecoverable JSONL in {path.name}.")
            ) from None
        if not isinstance(parsed, dict):
            raise StateCorruptionError(
                _corruption_message(path, f"JSONL event must be an object in {path.name}.")
            )
        events.append(parsed)
    return events, repaired_tail


def atomic_write_jsonl(path: Path, items: list[dict[str, Any]]) -> None:
    content = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in items)
    backup = path.with_name(path.name + ".bak")
    if path.exists():
        current = path.read_text(encoding="utf-8")
        _parse_jsonl(current, path, allow_tail_repair=False)
        _atomic_replace_bytes(backup, current.encode("utf-8"))
    atomic_write_text(path, content)


def read_jsonl_recovering(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        atomic_write_text(path, "")
        return []
    text = path.read_text(encoding="utf-8")
    events, repaired_tail = _parse_jsonl(text, path, allow_tail_repair=True)
    if repaired_tail:
        content = "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in events)
        atomic_write_text(path, content)
    return events
