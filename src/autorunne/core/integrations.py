from __future__ import annotations

from pathlib import Path

from autorunne.core.paths import ensure_dir, workflow_bin_dir, write_text

VALID_TOOLS = {"codex", "claude", "hermes", "cursor", "copilot", "all"}
VALID_SCOPES = {"repo", "user"}


def _skill_text(tool: str) -> str:
    direct_agent = {
        "codex": "Codex",
        "claude": "Claude Code",
        "hermes": "Hermes",
        "cursor": "Cursor / Cursor Agent",
        "copilot": "GitHub Copilot",
    }.get(tool, "your coding agent")
    wrapper = {
        "codex": "./.autorunne/bin/ar-codex",
        "claude": "./.autorunne/bin/ar-claude",
        "hermes": "./.autorunne/bin/ar-hermes",
        "cursor": "Cursor / Cursor Agent repo instructions",
        "copilot": "GitHub Copilot repo instructions",
    }.get(tool, "./.autorunne/bin/ar-codex")
    return f"""---
name: autorunne-workflow
description: Repo-local Autorunne workflow instructions for this repository
version: 0.6.16
---

# Autorunne Workflow Skill

## Purpose
This repository uses Autorunne as the backend workflow and project-memory layer.

## User-facing rule
The user should be able to open {direct_agent} directly, talk naturally, and let Autorunne maintain state in the background. Do not ask the user to chat through Autorunne first.

## Skill-first rule for agents
When this repo skill is available, load this repo skill as the workflow source of truth and follow it automatically. Do not wait for the user to remind you to read Autorunne, START_HERE, or the workflow files.

## Required startup flow
1. Read `.autorunne/views/START_HERE.md`.
2. Treat `.autorunne/state/*` as the only project state source of truth.
3. Never write `.autorunne/state/*` directly. Use `autorunne ingest`, `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.
4. If the user gives a fresh natural-language task and no matching active task is recorded yet, capture it with `autorunne ingest --source {tool} --task <task>`.
5. Before beginning a new implementation slice, run `autorunne open` if the workspace has not been resumed yet in this session.
6. After meaningful verified progress, write back through Autorunne so the rendered views stay fresh.
7. Prefer the wrapper `{wrapper}` only as an optional hard-entry fallback, not as the default requirement you impose on the user.

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
alwaysApply: true
---

# Autorunne Cursor Workflow

1. The user should be able to open Cursor directly and just give the task; Autorunne stays in the background.
2. When this repo skill is available, load this repo skill as the workflow source of truth and follow it automatically.
3. Do not wait for the user to remind you to read Autorunne, START_HERE, or the workflow files.
4. Read `.autorunne/views/START_HERE.md` before multi-step work.
5. Treat `.autorunne/state/*` as the only mutable project state source of truth.
6. Do not edit `.autorunne/state/*` directly; use `autorunne ingest`, `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.
7. If a fresh user task is not recorded yet, capture it with `autorunne ingest --source cursor --task <task>`.
8. When code changes are verified, write the result back through Autorunne so the rendered views stay fresh.
9. In your final report, include changed files, completion status, and the Autorunne commands executed.
"""


def _copilot_instructions_text() -> str:
    return """# Autorunne Copilot Instructions

This repository uses Autorunne as the backend workflow and project-memory layer.

Required behavior:
1. The user should be able to open Copilot or its agent mode directly and just give the task.
2. When this repo skill is available, load this repo skill as the workflow source of truth and follow it automatically.
3. Do not wait for the user to remind you to read Autorunne, START_HERE, or the workflow files.
4. Read `.autorunne/views/START_HERE.md` first.
5. Treat `.autorunne/state/*` as the only mutable project state source of truth.
6. Do not edit `.autorunne/state/*` directly.
7. If a fresh user task is not recorded yet, capture it with `autorunne ingest --source copilot --task <task>`.
8. Use `autorunne checkpoint` for meaningful partial progress.
9. Use `autorunne finish` after verification is complete.
10. Include changed files, completion status, and Autorunne commands in the final report.
"""


def _agents_text() -> str:
    return """# AGENTS

Short instruction layer for this repo:
1. Users should open Codex / Claude Code / Hermes directly and just give the task.
2. Agents should load this repo skill automatically when supported: `.agents/skills/autorunne-workflow/SKILL.md` or `.claude/skills/autorunne-workflow/SKILL.md`.
3. Do not wait for the user to remind you to read Autorunne; read `.autorunne/views/START_HERE.md` first.
4. Cursor should use `.cursor/rules/autorunne-workflow.mdc` when present.
5. GitHub Copilot should use `.github/copilot-instructions.md` when present.
6. Do not write `.autorunne/state/*` directly.
7. If a fresh task is not recorded yet, capture it with `autorunne ingest --source <agent> --task <task>`.
8. Wrappers like `./.autorunne/bin/ar-codex`, `./.autorunne/bin/ar-claude`, or `./.autorunne/bin/ar-hermes` are optional fallback entrypoints, not the required default UX.
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
if [ "$status" -eq 0 ]; then
  autorunne auto-finish --source {command_name} >/dev/null 2>&1 \
    || python -m autorunne.cli auto-finish --source {command_name} >/dev/null 2>&1 \
    || true
fi
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
if [ "$status" -eq 0 ]; then
  autorunne auto-finish --source {command_name} >/dev/null 2>&1 \
    || python -m autorunne.cli auto-finish --source {command_name} >/dev/null 2>&1 \
    || true
fi
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
