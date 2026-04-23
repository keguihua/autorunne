from __future__ import annotations

import time
from pathlib import Path

from autorunne.commands import open as open_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.core.auto_record import auto_record_local_change
from autorunne.core.filewatch import diff_snapshots, snapshot_tree
from autorunne.core.gitops import detect_repo_root


def run(target: Path, duration: float = 30.0, interval: float = 1.0, max_syncs: int | None = None) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne daemon must run inside an existing git repository")

    open_result = open_cmd.run(repo_root)
    previous = snapshot_tree(repo_root)
    start = time.time()
    ticks = 0
    syncs = 0
    auto_records = 0
    last_sync = None
    last_changed_files: list[str] = []
    last_auto_summary = None
    next_action = open_result["scan"]["next_action"]

    while time.time() - start < duration:
        time.sleep(interval)
        ticks += 1
        current = snapshot_tree(repo_root)
        if current != previous:
            last_changed_files = diff_snapshots(previous, current)
            changed_summary = ", ".join(last_changed_files[:5])
            note = f"daemon auto-sync: {changed_summary}" if changed_summary else "daemon auto-sync"
            sync_result = sync_cmd.run(repo_root, note=note)
            syncs += 1
            last_sync = sync_result["repo_root"]
            next_action = sync_result["scan"]["next_action"]
            auto_record_result = auto_record_local_change(repo_root, changed_files=last_changed_files, source="daemon")
            if auto_record_result["auto_recorded"]:
                auto_records += 1
                last_auto_summary = auto_record_result["summary"]
            previous = current
            if max_syncs is not None and syncs >= max_syncs:
                break
        else:
            previous = current

    return {
        "repo_root": str(repo_root),
        "action": open_result["action"],
        "ticks": ticks,
        "syncs": syncs,
        "auto_records": auto_records,
        "last_sync": last_sync,
        "last_changed_files": last_changed_files,
        "last_auto_summary": last_auto_summary,
        "next_action": next_action,
    }
