from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autorunne import __version__ as AUTORUNNE_VERSION
from autorunne.models.config import WorkflowConfig

CONFIG_FILENAME = "config.json"
WORKFLOW_DIR = ".autorunne"
STATE_DIRNAME = "state"
VIEWS_DIRNAME = "views"
SNAPSHOTS_DIRNAME = "snapshots"
AGENTS_DIRNAME = "agents"
BIN_DIRNAME = "bin"
STATE_FILES = [
    "current.json",
    "events.jsonl",
    "tasks.json",
    "decisions.json",
    "sessions.json",
]
VIEW_FILES = [
    "PROJECT_CONTEXT.md",
    "TASKS.md",
    "DECISIONS.md",
    "SESSION_LOG.md",
    "RULES.md",
    "NEXT_ACTION.md",
    "COMMANDS.md",
    "START_HERE.md",
    "STATUS.md",
]


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def workflow_dir(repo_root: Path) -> Path:
    return repo_root / WORKFLOW_DIR


def workflow_file(repo_root: Path, name: str) -> Path:
    return workflow_dir(repo_root) / name


def state_dir(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / STATE_DIRNAME


def state_file(repo_root: Path, name: str) -> Path:
    return state_dir(repo_root) / name


def views_dir(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / VIEWS_DIRNAME


def view_file(repo_root: Path, name: str) -> Path:
    return views_dir(repo_root) / name


def agents_dir(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / AGENTS_DIRNAME


def workflow_bin_dir(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / BIN_DIRNAME


def snapshots_dir(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / SNAPSHOTS_DIRNAME


def snapshot_file(repo_root: Path, name: str = "latest.json") -> Path:
    return snapshots_dir(repo_root) / name


def config_path(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / CONFIG_FILENAME


def load_config(repo_root: Path) -> WorkflowConfig:
    path = config_path(repo_root)
    if path.exists():
        return WorkflowConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
    return WorkflowConfig()


def migrate_config(repo_root: Path) -> dict[str, Any]:
    """Safely bring `.autorunne/config.json` up to the running package version.

    This only touches the config file: existing user values and unknown keys are
    preserved, missing modern defaults are added, and the version field is set to
    the installed Autorunne package version. It does not remove state, reports,
    runtime files, skills, or rendered views.
    """
    path = config_path(repo_root)
    defaults = WorkflowConfig().model_dump()
    existing: dict[str, Any] = {}
    if path.exists():
        existing = json.loads(path.read_text(encoding="utf-8"))
    merged = {**defaults, **existing}
    merged["version"] = AUTORUNNE_VERSION
    if merged != existing:
        ensure_dir(workflow_dir(repo_root))
        path.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return {"path": str(path), "updated": merged != existing, "version": merged["version"]}


def save_config(repo_root: Path, config: WorkflowConfig) -> Path:
    ensure_dir(workflow_dir(repo_root))
    path = config_path(repo_root)
    path.write_text(json.dumps(config.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def read_json(path: Path, default: Any | None = None) -> Any:
    if not path.exists():
        return {} if default is None else default
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
