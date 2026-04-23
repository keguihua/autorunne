from __future__ import annotations

import time
from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.auto_record import auto_record_local_change
from autorunne.core.filewatch import diff_snapshots, snapshot_tree
from autorunne.commands import sync as sync_cmd


def run(target: Path, duration: float = 30.0, interval: float = 1.0) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne watch must run inside an existing git repository")

    start = time.time()
    previous = snapshot_tree(repo_root)
    changes = 0
    auto_records = 0
    last_sync = None
    last_changed_files: list[str] = []
    last_auto_summary = None

    while time.time() - start < duration:
        time.sleep(interval)
        current = snapshot_tree(repo_root)
        if current != previous:
            changes += 1
            last_changed_files = diff_snapshots(previous, current)
            changed_summary = ", ".join(last_changed_files[:5])
            note = f"watch auto-sync: {changed_summary}" if changed_summary else "watch auto-sync"
            sync_result = sync_cmd.run(repo_root, note=note)
            last_sync = sync_result["repo_root"]
            auto_record_result = auto_record_local_change(repo_root, changed_files=last_changed_files, source="watch")
            if auto_record_result["auto_recorded"]:
                auto_records += 1
                last_auto_summary = auto_record_result["summary"]
            previous = current
        else:
            previous = current

    return {
        "repo_root": str(repo_root),
        "changes_detected": changes,
        "auto_records": auto_records,
        "last_sync": last_sync,
        "last_changed_files": last_changed_files,
        "last_auto_summary": last_auto_summary,
        "duration": duration,
    }
