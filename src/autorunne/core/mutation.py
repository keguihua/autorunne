from __future__ import annotations

from collections.abc import Callable
from functools import wraps
from pathlib import Path
from typing import Any, TypeVar

from autorunne.core.persistence import workspace_lock

F = TypeVar("F", bound=Callable[..., Any])


def state_mutator(function: F) -> F:
    """Hold the workspace lock, finish any pending compact, then mutate."""

    @wraps(function)
    def wrapped(repo_root: Path, *args: Any, **kwargs: Any):
        with workspace_lock(repo_root):
            from autorunne.core.memory import recover_pending_compaction

            recover_pending_compaction(repo_root)
            return function(repo_root, *args, **kwargs)

    return wrapped  # type: ignore[return-value]
