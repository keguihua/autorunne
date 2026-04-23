from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import ensure_dir, workflow_bin_dir, write_text

VALID_TOOLS = {"codex", "claude", "hermes", "cursor", "copilot", "all"}
VALID_SCOPES = {"repo", "user"}


def _skill_text(tool: str) -> str:
    wrapper = {
        "codex": "./.autorunne/bin/ar-codex",
        "claude": "./.autorunne/bin/ar-claude",
        "hermes": "./.autorunne/bin/ar-hermes",
        "cursor": "Cursor / Cursor Agent repo instructions",
        "copilot": "GitHub Copilot repo instructions",
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


def _cursor_rules_text() -> str:
    return """---
description: Autorunne workflow contract for this repo
globs:
alwaysApply: true
---

# Autorunne Cursor Workflow

1. Read `.autorunne/views/START_HERE.md` before multi-step work.
2. Treat `.autorunne/state/*` as the only mutable project state source of truth.
3. Do not edit `.autorunne/state/*` directly; use `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.
4. When code changes are verified, write the result back through Autorunne so the rendered views stay fresh.
5. In your final report, include changed files, completion status, and the Autorunne commands executed.
"""


def _copilot_instructions_text() -> str:
    return """# Autorunne Copilot Instructions

This repository uses Autorunne as the workflow and project-memory layer.

Required behavior:
1. Read `.autorunne/views/START_HERE.md` first.
2. Treat `.autorunne/state/*` as the only mutable project state source of truth.
3. Do not edit `.autorunne/state/*` directly.
4. Use `autorunne start` when the task has not been recorded yet.
5. Use `autorunne checkpoint` for meaningful partial progress.
6. Use `autorunne finish` after verification is complete.
7. Include changed files, completion status, and Autorunne commands in the final report.
"""


def _agents_text() -> str:
    return """# AGENTS

Short instruction layer for this repo:
1. Read `.autorunne/views/START_HERE.md` first.
2. Use repo skill files under `.agents/skills/autorunne-workflow/` or `.claude/skills/autorunne-workflow/`.
3. Cursor should use `.cursor/rules/autorunne-workflow.mdc` when present.
4. GitHub Copilot should use `.github/copilot-instructions.md` when present.
5. Do not write `.autorunne/state/*` directly.
6. Prefer `./.autorunne/bin/ar-codex`, `./.autorunne/bin/ar-claude`, or `./.autorunne/bin/ar-hermes` for a hard Autorunne entry.
"""


def _wrapper_script(command_name: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
REPO_ROOT=\"$(cd \"$(dirname \"${{BASH_SOURCE[0]}}\")/../..\" && pwd)\"
cd \"$REPO_ROOT\"
autorunne open >/dev/null 2>&1 || python -m autorunne.cli open >/dev/null 2>&1
AUTORUNNE_DAEMON_PID=\"\"
if [ "${{AUTORUNNE_DISABLE_DAEMON:-0}}" != "1" ] && [ "${{AUTORUNNE_DAEMON_ACTIVE:-0}}" != "1" ]; then
  export AUTORUNNE_DAEMON_ACTIVE=1
  DAEMON_DURATION="${{AUTORUNNE_DAEMON_DURATION:-43200}}"
  DAEMON_INTERVAL="${{AUTORUNNE_DAEMON_INTERVAL:-1}}"
  (
    autorunne daemon --duration "$DAEMON_DURATION" --interval "$DAEMON_INTERVAL" >/dev/null 2>&1 \
      || python -m autorunne.cli daemon --duration "$DAEMON_DURATION" --interval "$DAEMON_INTERVAL" >/dev/null 2>&1
  ) &
  AUTORUNNE_DAEMON_PID=$!
fi
cleanup() {{
  if [ -n "${{AUTORUNNE_DAEMON_PID}}" ]; then
    kill "${{AUTORUNNE_DAEMON_PID}}" >/dev/null 2>&1 || true
  fi
}}
trap cleanup EXIT INT TERM
set +e
{command_name} "$@"
status=$?
set -e
cleanup
exit $status
"""


def _user_wrapper_script(command_name: str) -> str:
    return f"""#!/usr/bin/env bash
set -euo pipefail
autorunne open >/dev/null 2>&1 || python -m autorunne.cli open >/dev/null 2>&1
AUTORUNNE_DAEMON_PID=\"\"
if [ "${{AUTORUNNE_DISABLE_DAEMON:-0}}" != "1" ] && [ "${{AUTORUNNE_DAEMON_ACTIVE:-0}}" != "1" ]; then
  export AUTORUNNE_DAEMON_ACTIVE=1
  DAEMON_DURATION="${{AUTORUNNE_DAEMON_DURATION:-43200}}"
  DAEMON_INTERVAL="${{AUTORUNNE_DAEMON_INTERVAL:-1}}"
  (
    autorunne daemon --duration "$DAEMON_DURATION" --interval "$DAEMON_INTERVAL" >/dev/null 2>&1 \
      || python -m autorunne.cli daemon --duration "$DAEMON_DURATION" --interval "$DAEMON_INTERVAL" >/dev/null 2>&1
  ) &
  AUTORUNNE_DAEMON_PID=$!
fi
cleanup() {{
  if [ -n "${{AUTORUNNE_DAEMON_PID}}" ]; then
    kill "${{AUTORUNNE_DAEMON_PID}}" >/dev/null 2>&1 || true
  fi
}}
trap cleanup EXIT INT TERM
set +e
{command_name} "$@"
status=$?
set -e
cleanup
exit $status
"""


def _tool_selection(tool: str) -> list[str]:
    if tool not in VALID_TOOLS:
        raise ValueError(f"Unsupported tool: {tool}")
    return ["codex", "claude", "hermes", "cursor", "copilot"] if tool == "all" else [tool]


def _target_roots(repo_root: Path, scope: str) -> dict[str, Path]:
    if scope not in VALID_SCOPES:
        raise ValueError(f"Unsupported scope: {scope}")
    if scope == "repo":
        return {
            "agents_root": repo_root / ".agents" / "skills" / "autorunne-workflow",
            "claude_root": repo_root / ".claude" / "skills" / "autorunne-workflow",
            "cursor_rules": repo_root / ".cursor" / "rules" / "autorunne-workflow.mdc",
            "copilot_instructions": repo_root / ".github" / "copilot-instructions.md",
            "bin_root": workflow_bin_dir(repo_root),
            "agents_md": repo_root / "AGENTS.md",
        }
    home = Path.home()
    return {
        "agents_root": home / ".agents" / "skills" / "autorunne-workflow",
        "claude_root": home / ".claude" / "skills" / "autorunne-workflow",
        "cursor_rules": home / ".cursor" / "rules" / "autorunne-workflow.mdc",
        "copilot_instructions": home / ".github" / "copilot-instructions.md",
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

    if "cursor" in selected:
        write_text(targets["cursor_rules"], _cursor_rules_text())
        created_paths.append(str(targets["cursor_rules"]))
        tools_installed.append("cursor")

    if "copilot" in selected:
        write_text(targets["copilot_instructions"], _copilot_instructions_text())
        created_paths.append(str(targets["copilot_instructions"]))
        tools_installed.append("copilot")

    wrapper_map = {
        "codex": "codex",
        "claude": "claude",
        "hermes": "hermes",
    }
    for name in selected:
        if name not in wrapper_map:
            continue
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
