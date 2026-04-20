from __future__ import annotations

import json
from pathlib import Path


def _merge_dict(base: dict, updates: dict) -> dict:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged


def install_vscode_integration(repo_root: Path) -> dict[str, str]:
    vscode_dir = repo_root / ".vscode"
    vscode_dir.mkdir(parents=True, exist_ok=True)

    settings_path = vscode_dir / "settings.json"
    tasks_path = vscode_dir / "tasks.json"
    extensions_path = vscode_dir / "extensions.json"

    existing_settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.exists() else {}
    settings = _merge_dict(
        existing_settings,
        {
            "task.allowAutomaticTasks": "on",
            "files.exclude": {"**/.autorunne": True},
        },
    )
    settings_path.write_text(json.dumps(settings, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    tasks = {
        "version": "2.0.0",
        "tasks": [
            {
                "label": "Autorunne: Sync on folder open",
                "type": "shell",
                "command": "autorunne sync || python -m autorunne.cli sync",
                "presentation": {"reveal": "never", "panel": "dedicated"},
                "problemMatcher": [],
                "runOptions": {"runOn": "folderOpen"},
            },
            {
                "label": "Autorunne: Status",
                "type": "shell",
                "command": "autorunne status || python -m autorunne.cli status",
                "presentation": {"reveal": "always", "panel": "shared"},
                "problemMatcher": [],
            },
        ],
    }
    tasks_path.write_text(json.dumps(tasks, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    extensions = {
        "recommendations": [
            "ms-python.python",
            "ms-vscode.makefile-tools",
        ]
    }
    extensions_path.write_text(json.dumps(extensions, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {
        "settings_path": str(settings_path),
        "tasks_path": str(tasks_path),
        "extensions_path": str(extensions_path),
    }
