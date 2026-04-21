from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.state_engine import mutate_task_list, workflow_exists

SECTION_ALIASES = {
    "next-up": "next_up",
    "next_up": "next_up",
    "known-unknowns": "known_unknowns",
    "known_unknowns": "known_unknowns",
    "in-progress": "in_progress",
    "in_progress": "in_progress",
    "completed": "completed",
}


def _normalize_section(section: str) -> str:
    normalized = SECTION_ALIASES.get(section, section)
    if normalized not in SECTION_ALIASES.values():
        raise ValueError(f"Unsupported task section: {section}")
    return normalized


def add(target: Path, *, text: str, section: str = "next-up") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne task add must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne task add requires an initialized Autorunne workspace")
    result = mutate_task_list(repo_root, action="add", text=text, section=_normalize_section(section))
    return {"repo_root": str(repo_root), **result["payload"]}


def done(target: Path, *, match: str, section: str = "next-up") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne task done must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne task done requires an initialized Autorunne workspace")
    result = mutate_task_list(repo_root, action="done", match=match, section=_normalize_section(section))
    return {"repo_root": str(repo_root), **result["payload"]}


def remove(target: Path, *, match: str, section: str = "next-up") -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne task remove must run inside an existing git repository")
    if not workflow_exists(repo_root):
        raise RuntimeError("autorunne task remove requires an initialized Autorunne workspace")
    result = mutate_task_list(repo_root, action="remove", match=match, section=_normalize_section(section))
    return {"repo_root": str(repo_root), **result["payload"]}
