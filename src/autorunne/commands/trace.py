from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import trace_events, workflow_exists


def run(target: Path, *, limit: int = 20, event_type: str | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne trace must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne trace requires an initialized Autorunne workspace")
    items = trace_events(repo_root, limit=limit, event_type=event_type)
    return {"repo_root": str(repo_root), "items": items}
