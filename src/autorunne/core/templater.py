from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from autorunne.core.paths import WORKFLOW_DIR


TEMPLATES = {
    "PROJECT_CONTEXT.md": """# Project Context

## Project
- Name: {repo_name}
- Stack: {stack}
- Framework: {framework}
- Package manager: {package_manager}
- Project phase: {project_phase}
- Tracked files: {tracked_files_count}

## Important files
{important_files}

## Important directories
{source_dirs}

## Current state
- Workflow initialized by Autorunne
- Repository type inferred from local scan
- Resume hint: {resume_hint}
- Confirm assumptions below before large changes

## Recent work signals
### Dirty / recently changed files
{recent_files}

### Recent commits
{recent_commits}

## Constraints
- Keep changes scoped to the current task
- Do not commit `{workflow_dir}` to the public repo
- Verify run/test commands before refactoring

## Manual confirmation needed
- Confirm the main runtime command
- Confirm the test command
- Confirm which modules are stable vs risky
""",
    "TASKS.md": """# Tasks

## Completed / inferred
{completed}

## In progress
- [ ] Validate local run and test commands

## Next up
- [ ] {next_action}

## Known unknowns
- [ ] Confirm deployment flow
- [ ] Confirm protected or high-risk modules before large edits
""",
    "DECISIONS.md": """# Decisions

## Baseline assumptions
- Project detected as: {stack}
- Main framework likely: {framework}
- Package manager likely: {package_manager}
- Project phase likely: {project_phase}

## Pending confirmations
- Confirm whether these detections are correct
- Record important architectural decisions here before large changes

## Recorded decisions
- Add durable project decisions here as they are confirmed.
""",
    "SESSION_LOG.md": """# Session Log

## {timestamp} | workflow initialized
- Mode: {mode}
- Repo: {repo_name}
- Stack: {stack}
- Framework: {framework}
- Project phase: {project_phase}
- Next action: {next_action}
""",
    "RULES.md": """# Rules

1. Read `PROJECT_CONTEXT.md`, `TASKS.md`, and the latest `SESSION_LOG.md` before coding.
2. Only change files related to the current task.
3. Prefer the smallest safe change over broad refactors.
4. Run the relevant validation command after each meaningful change.
5. Update workflow docs after finishing a task.
6. Keep `{workflow_dir}` local-only.
""",
    "NEXT_ACTION.md": """# Next Action

{next_action}
""",
    "COMMANDS.md": """# Commands

## Detected local commands
{commands_markdown}

## Auto-open loop
1. Run `autorunne open` when you enter the repo.
2. If `.autorunne/` does not exist yet, Autorunne bootstraps it automatically.
3. If the repo already has workflow memory, Autorunne refreshes it and resumes from `NEXT_ACTION.md`.
4. End each slice with `autorunne checkpoint` or `autorunne finish`.
""",
    "START_HERE.md": """# Start Here

Autorunne is built to work with **Claude Code**, **Codex**, **Gemini**, **Hermes**, **Cursor**, and **GitHub Copilot** in a normal repo folder or VS Code terminal.

## Open-first workflow
- Run `autorunne open` whenever you enter this repo.
- In VS Code, install the generated workspace task once so folder open can trigger Autorunne automatically.
- Autorunne will bootstrap `.autorunne/` for half-finished repos and refresh existing memory on every open.
- You can launch Codex or Claude Code directly from this repo terminal after that; Autorunne does not need its own extra window unless you want daemon mode.

## Read these files first
- `PROJECT_CONTEXT.md`
- `TASKS.md`
- `DECISIONS.md`
- `NEXT_ACTION.md`
- `COMMANDS.md`

## Current focus
- Next action: {next_action}
- Stack: {stack}
- Framework: {framework}
- Project phase: {project_phase}
- Resume hint: {resume_hint}

## Zero-prompt handoff
If your coding agent can read repo files, just point it at this folder and ask it to continue from `.autorunne/START_HERE.md`.

## Recommended local commands
{commands_markdown}
""",
}

AGENT_TEMPLATES = {
    "common.md": """# Common Agent Rules

- Read the shared workflow files before changing code.
- Ask for clarification when a risky change is unclear.
- Keep edits minimal and traceable.
- Update task and session state after work is done.
""",
    "claude-code.md": """# Claude Code Adapter

- Start with the shared workflow files under `.autorunne/`.
- Explain planned scope before broad edits.
- Prefer small patches over rewrites.
""",
    "codex.md": """# Codex Adapter

- Use the shared workflow files as the single source of truth.
- Avoid opportunistic refactors unless explicitly requested.
- After coding, summarize changed files and update workflow docs.
""",
    "hermes.md": """# Hermes Adapter

- Load project context from `.autorunne/` first.
- Use the next action as the default starting point.
- Keep project memory synced after each task.
""",
    "cursor.md": """# Cursor Adapter

- Read shared workflow docs before agent edits.
- Keep changes narrow and validate locally.
- Reflect completed work back into `.autorunne/`.
""",
    "copilot.md": """# GitHub Copilot Adapter

- Use `.autorunne/START_HERE.md` as the fastest entry point.
- Read the shared workflow docs before generating or editing code.
- Prefer small, testable changes and update `checkpoint` or `finish` after each meaningful slice.
""",
}


def _bulletize(items: Iterable[str], default: str) -> str:
    values = list(items)
    if not values:
        values = [default]
    return "\n".join(f"- {item}" for item in values)


def _render_commands(scan: dict) -> str:
    commands = scan.get("commands", {})
    ordered = [
        ("run", "Run"),
        ("test", "Test"),
        ("build", "Build"),
        ("configure", "Configure"),
    ]
    lines = []
    for key, label in ordered:
        if commands.get(key):
            lines.append(f"- **{label}:** `{commands[key]}`")
    if not lines:
        lines.append("- No reliable run/test/build commands detected yet. Confirm them manually.")
    return "\n".join(lines)


def render_bundle(scan: dict, mode: str) -> dict[str, str]:
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    context = {
        "repo_name": scan["repo_name"],
        "stack": ", ".join(scan["stack"]),
        "framework": ", ".join(scan["framework"]),
        "package_manager": ", ".join(scan["package_manager"]),
        "important_files": _bulletize(scan["important_files"], "No obvious entry files detected"),
        "source_dirs": _bulletize(scan["source_dirs"], "No common source directories detected"),
        "completed": _bulletize([
            f"Detected stack: {', '.join(scan['stack'])}",
            f"Detected framework: {', '.join(scan['framework'])}",
            f"Detected package manager: {', '.join(scan['package_manager'])}",
            f"Detected project phase: {scan['project_phase']}",
        ], "Initial scan complete"),
        "next_action": scan["next_action"],
        "mode": mode,
        "timestamp": timestamp,
        "workflow_dir": WORKFLOW_DIR,
        "commands_markdown": _render_commands(scan),
        "project_phase": scan["project_phase"],
        "tracked_files_count": scan["tracked_files_count"],
        "resume_hint": scan["resume_hint"],
        "recent_files": _bulletize(scan["recent_files"], "No dirty files detected right now"),
        "recent_commits": _bulletize(scan["recent_commits"], "No recent commits detected yet"),
    }
    rendered = {name: template.format(**context) for name, template in TEMPLATES.items()}
    rendered.update({f"agents/{name}": template for name, template in AGENT_TEMPLATES.items()})
    return rendered
