from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import ensure_dir, workflow_bin_dir, write_text

VALID_TOOLS = {"codex", "claude", "hermes", "all"}
VALID_SCOPES = {"repo", "user"}


def _skill_text(tool: str) -> str:
    wrapper = {
        "codex": "./.autorunne/bin/ar-codex",
        "claude": "./.autorunne/bin/ar-claude",
        "hermes": "./.autorunne/bin/ar-hermes",
    }.get(tool, "./.autorunne/bin/ar-codex")
    return f"""# Autorunne Workflow Skill

## Purpose
This repository uses Autorunne as the state layer.

## Required startup flow
1. Read `.autorunne/views/START_HERE.md`.
2. Treat `.autorunne/state/*` as the only project state source of truth.
3. Never write `.autorunne/state/*` directly. Use `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.
4. Before beginning a new implementation slice, run `autorunne open` or use `{wrapper}`.
5. After meaningful verified progress, write back through Autorunne so the rendered views stay fresh.

## Read order
1. `.autorunne/views/START_HERE.md`
2. `.autorunne/views/PROJECT_CONTEXT.md`
3. `.autorunne/views/TASKS.md`
4. `.autorunne/views/DECISIONS.md`
5. `.autorunne/views/NEXT_ACTION.md`
"""


def _agents_text() -> str:
    return """# AGENTS

Short instruction layer for this repo:
1. Read `.autorunne/views/START_HERE.md` first.
2. Use repo skill files under `.agents/skills/autorunne-workflow/` or `.claude/skills/autorunne-workflow/`.
3. Do not write `.autorunne/state/*` directly.
4. Prefer `./.autorunne/bin/ar-codex`, `./.autorunne/bin/ar-claude`, or `./.autorunne/bin/ar-hermes` for a hard Autorunne entry.
"""


def _wrapper_script(command_name: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/../..\" && pwd)\"
cd \"$REPO_ROOT\"
autorunne open >/dev/null 2>&1 || python -m autorunne.cli open >/dev/null 2>&1
exec {command_name} "$@"
"""


def _user_wrapper_script(command_name: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
autorunne open >/dev/null 2>&1 || python -m autorunne.cli open >/dev/null 2>&1
exec {command_name} "$@"
"""


def _tool_selection(tool: str) -> list[str]:
    if tool not in VALID_TOOLS:
        raise ValueError(f"Unsupported tool: {tool}")
    return ["codex", "claude", "hermes"] if tool == "all" else [tool]


def _target_roots(repo_root: Path, scope: str) -> dict[str, Path]:
    if scope not in VALID_SCOPES:
        raise ValueError(f"Unsupported scope: {scope}")
    if scope == "repo":
        return {
            "agents_root": repo_root / ".agents" / "skills" / "autorunne-workflow",
            "claude_root": repo_root / ".claude" / "skills" / "autorunne-workflow",
            "bin_root": workflow_bin_dir(repo_root),
            "agents_md": repo_root / "AGENTS.md",
        }
    home = Path.home()
    return {
        "agents_root": home / ".agents" / "skills" / "autorunne-workflow",
        "claude_root": home / ".claude" / "skills" / "autorunne-workflow",
        "bin_root": home / ".local" / "bin",
        "agents_md": home / ".config" / "autorunne" / "AGENTS.md",
    }


def install_integrations(repo_root: Path, *, tool: str = "all", scope: str = "repo") -> dict:
    targets = _target_roots(repo_root, scope)
    selected = _tool_selection(tool)
    ensure_dir(targets["bin_root"])
    ensure_dir(targets["agents_root"])
    ensure_dir(targets["claude_root"])
    write_text(targets["agents_md"], _agents_text())

    created_paths = [str(targets["agents_md"])]
    tools_installed: list[str] = []
    wrappers: list[str] = []

    if any(name in selected for name in ["codex", "hermes"]):
        skill_path = targets["agents_root"] / "SKILL.md"
        write_text(skill_path, _skill_text("codex"))
        created_paths.append(str(skill_path))
        tools_installed.append("codex")

    if "claude" in selected:
        skill_path = targets["claude_root"] / "SKILL.md"
        write_text(skill_path, _skill_text("claude"))
        created_paths.append(str(skill_path))
        tools_installed.append("claude")

    wrapper_map = {
        "codex": "codex",
        "claude": "claude",
        "hermes": "hermes",
    }
    for name in selected:
        wrapper_name = f"ar-{name}"
        wrapper_path = targets["bin_root"] / wrapper_name
        content = _wrapper_script(wrapper_map[name]) if scope == "repo" else _user_wrapper_script(wrapper_map[name])
        write_text(wrapper_path, content)
        wrapper_path.chmod(0o755)
        created_paths.append(str(wrapper_path))
        wrappers.append(wrapper_name)
        if name not in tools_installed:
            tools_installed.append(name)

    return {
        "scope": scope,
        "tool": tool,
        "tools": sorted(set(tools_installed)),
        "wrappers": wrappers,
        "paths": created_paths,
    }
