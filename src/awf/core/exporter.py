from __future__ import annotations

import shutil
from pathlib import Path

from awf.core.paths import load_config


def export_clean_copy(repo_root: Path, output_name: str | None = None) -> Path:
    config = load_config(repo_root)
    export_root = repo_root / config.export_dir
    export_root.mkdir(parents=True, exist_ok=True)
    target = export_root / (output_name or repo_root.name)
    if target.exists():
        shutil.rmtree(target)

    excluded = set(config.excluded_paths)

    def ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        for name in names:
            if name in excluded:
                ignored.add(name)
        return ignored

    shutil.copytree(repo_root, target, ignore=ignore)
    return target
