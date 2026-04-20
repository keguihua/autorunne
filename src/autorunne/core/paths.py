from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from autorunne.models.config import WorkflowConfig

CONFIG_FILENAME = "config.json"
WORKFLOW_DIR = ".autorunne"


def ensure_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def workflow_dir(repo_root: Path) -> Path:
    return repo_root / WORKFLOW_DIR


def workflow_file(repo_root: Path, name: str) -> Path:
    return workflow_dir(repo_root) / name


def config_path(repo_root: Path) -> Path:
    return workflow_dir(repo_root) / CONFIG_FILENAME


def load_config(repo_root: Path) -> WorkflowConfig:
    path = config_path(repo_root)
    if path.exists():
        return WorkflowConfig.model_validate(json.loads(path.read_text(encoding="utf-8")))
    return WorkflowConfig()


def save_config(repo_root: Path, config: WorkflowConfig) -> Path:
    ensure_dir(workflow_dir(repo_root))
    path = config_path(repo_root)
    path.write_text(json.dumps(config.model_dump(), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return path


def write_json(path: Path, payload: Any) -> None:
    ensure_dir(path.parent)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_text(path: Path, content: str) -> None:
    ensure_dir(path.parent)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")
