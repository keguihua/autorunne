from __future__ import annotations

from typing import Iterable


def _bulletize(items: Iterable[str], default: str) -> str:
    values = [str(item).strip() for item in items if str(item).strip()]
    if not values:
        values = [default]
    return "\n".join(f"- {item}" for item in values)


def _script_command(package_path: str, script_name: str, package_manager: str = "npm") -> str:
    prefix = f"cd {package_path} && " if package_path != "." else ""
    if script_name == "test":
        return f"{prefix}{package_manager} test"
    if script_name == "start":
        return f"{prefix}{package_manager} start"
    return f"{prefix}{package_manager} run {script_name}"


def _package_summary(current: dict) -> dict:
    packages = current.get("packages") or []
    if not packages:
        return current
    derived = dict(current)
    frameworks = []
    source_dirs = []
    important_files = []
    commands = dict(current.get("commands") or {})
    package_manager = "npm per package"
    for package in packages:
        path = str(package.get("path", "")).strip()
        if not path:
            continue
        package_type = package.get("type") or package.get("framework") or "Node.js package"
        if package_type not in frameworks:
            frameworks.append(package_type)
        source_dirs.append(path)
        important_files.append(f"{path}/package.json")
        pm = package.get("package_manager") or "npm"
        package_manager = f"{pm} per package"
        for script_name in (package.get("scripts") or {}):
            commands.setdefault(f"{path}:{script_name}", _script_command(path, script_name, pm))
    if derived.get("stack") in ([], ["generic"], None):
        derived["stack"] = ["multi-package Node/TypeScript"]
    if derived.get("framework") in ([], ["generic"], None):
        derived["framework"] = frameworks or ["Node.js package"]
    if derived.get("package_manager") in ([], ["unknown"], None):
        derived["package_manager"] = [package_manager]
    derived["source_dirs"] = list(dict.fromkeys([*source_dirs, *derived.get("source_dirs", [])]))
    derived["important_files"] = list(dict.fromkeys([*important_files, *derived.get("important_files", [])]))
    derived["commands"] = commands
    return derived


def _render_commands(commands: dict) -> str:
    ordered = [
        ("run", "Run"),
        ("test", "Test"),
        ("build", "Build"),
        ("configure", "Configure"),
    ]
    lines = []
    rendered_keys = set()
    for key, label in ordered:
        value = commands.get(key)
        if value:
            lines.append(f"- **{label}:** `{value}`")
            rendered_keys.add(key)
    for key in sorted(k for k in commands if k not in rendered_keys):
        value = commands.get(key)
        if value:
            lines.append(f"- **{key}:** `{value}`")
    if not lines:
        lines.append("- No reliable run/test/build commands detected yet. Confirm them manually.")
    return "\n".join(lines)


def _render_task_lines(items: list[dict], default: str | None = None) -> str:
    if not items:
        return f"- [ ] {default}" if default else "- none"
    lines = []
    for item in items:
        status = item.get("status", "pending")
        checked = "x" if status in {"completed", "archived"} else " "
        lines.append(f"- [{checked}] {item.get('text', '').strip()}")
    return "\n".join(lines)


def _render_session_lines(session: dict) -> str:
    lines = [f"## {session['timestamp']} | {session['title']}"]
    for line in session.get("lines", []):
        lines.append(f"- {line}")
    return "\n".join(lines)


def render_view_bundle(state: dict) -> dict[str, str]:
    current = _package_summary(state["current"])
    tasks = state["tasks"]
    decisions = state["decisions"]
    sessions = state["sessions"]

    integrations = current.get("integrations", {})
    repo_integrations = integrations.get("repo", {})
    repo_tools = ", ".join(repo_integrations.get("tools", [])) or "not installed yet"
    repo_wrappers = repo_integrations.get("wrappers", [])
    wrapper_lines = _bulletize(repo_wrappers, "No wrappers installed yet")
    commands_markdown = _render_commands(current.get("commands", {}))
    views_root = ".autorunne/views"
    agents_root = ".autorunne/agents"

    project_context = f"""# Project Context

## Project
- Name: {current['repo_name']}
- Stack: {', '.join(current.get('stack', []))}
- Framework: {', '.join(current.get('framework', []))}
- Package manager: {', '.join(current.get('package_manager', []))}
- Project phase: {current.get('project_phase', 'unknown')}
- Tracked files: {current.get('tracked_files_count', 0)}

## Important files
{_bulletize(current.get('important_files', []), 'No obvious entry files detected')}

## Important directories
{_bulletize(current.get('source_dirs', []), 'No common source directories detected')}

## Current state
- `.autorunne/state/*` is the source of truth.
- `{views_root}/*.md` are rendered views only.
- Last action: {current.get('last_action', 'workspace_bootstrapped')}
- Resume hint: {current.get('resume_hint', 'Confirm the smallest safe next step first.')}
- Active task: {current.get('active_task') or 'none'}

## Recent work signals
### Dirty / recently changed files
{_bulletize(current.get('recent_files', []), 'No dirty files detected right now')}

### Recent commits
{_bulletize(current.get('recent_commits', []), 'No recent commits detected yet')}

## Integrations
- Repo-level tools installed: {repo_tools}
- Wrapper entrypoints live under `.autorunne/bin/`
- Primary wrapper list:
{wrapper_lines}
"""

    tasks_md = f"""# Tasks

## Completed / inferred
{_render_task_lines(tasks.get('completed', []), default='No completed tasks recorded yet')}

## In progress
{_render_task_lines(tasks.get('in_progress', []), default='No task in progress right now')}

## Next up
{_render_task_lines(tasks.get('next_up', []), default=current.get('next_action', 'Confirm the next concrete step.'))}

## Archived / historical
{_render_task_lines(tasks.get('archived', []), default='No archived backlog recorded yet')}

## Known unknowns
{_render_task_lines(tasks.get('known_unknowns', []), default='No known unknowns recorded yet')}
"""

    baseline = [f"- {line}" for line in decisions.get('baseline', [])]
    recorded = [f"- {item['timestamp']}: {item['text']}" for item in decisions.get('items', [])]
    decisions_md = "# Decisions\n\n## Baseline assumptions\n"
    decisions_md += "\n".join(baseline or ["- No baseline assumptions captured yet"]) + "\n\n"
    decisions_md += "## Recorded decisions\n"
    decisions_md += "\n".join(recorded or ["- No durable decisions recorded yet"]) + "\n"

    session_items = sessions.get('items', [])
    session_log = "# Session Log\n\n"
    if session_items:
        session_log += "\n\n".join(_render_session_lines(item) for item in session_items)
    else:
        session_log += "## No session entries yet\n- Bootstrap the workspace first."
    session_log += "\n"

    rules_md = f"""# Rules

1. Read `{views_root}/START_HERE.md` before multi-step work.
2. Treat `.autorunne/state/*` as the only mutable project memory.
3. Do not write state directly from skills or wrappers; go through Autorunne commands.
4. Prefer the smallest safe change over broad refactors.
5. Run the relevant validation command after each meaningful change.
6. Keep `.autorunne/` local-only unless the user explicitly wants it tracked.
"""

    next_action_md = f"# Next Action\n\n{current.get('next_action', 'Confirm the next concrete step.')}\n"

    commands_md = f"""# Commands

## Detected local commands
{commands_markdown}

## Open-first workflow
1. Open Codex / Claude Code / Hermes directly in the repo, or run `autorunne open` when you want to refresh the workspace explicitly.
2. All supported agents should read `{views_root}/START_HERE.md` and `{agents_root}/autorunne-workflow.md` first.
3. If the user gives a fresh natural-language task and no matching active task exists yet, capture it with `autorunne ingest --source <agent> --task <task>`.
4. Wrappers like `./.autorunne/bin/ar-codex` or `./.autorunne/bin/ar-claude` are optional hard-entry fallbacks, not the default UX.
5. Cursor should use `.cursor/rules/autorunne-workflow.mdc` when present.
6. GitHub Copilot should use `.github/copilot-instructions.md` when present.
7. End each slice with `autorunne checkpoint` or `autorunne finish`.
"""

    start_here_md = f"""# Start Here

Autorunne is the state layer for this repository, designed to work with Claude Code, Codex, Gemini, Hermes, Cursor, and GitHub Copilot.

## Read order
1. `{agents_root}/autorunne-workflow.md`
2. `{views_root}/PROJECT_CONTEXT.md`
3. `{views_root}/TASKS.md`
4. `{views_root}/DECISIONS.md`
5. `{views_root}/NEXT_ACTION.md`
6. `{views_root}/COMMANDS.md`

## Current focus
- Next action: {current.get('next_action', 'Confirm the next concrete step.')}
- Stack: {', '.join(current.get('stack', []))}
- Framework: {', '.join(current.get('framework', []))}
- Project phase: {current.get('project_phase', 'unknown')}
- Resume hint: {current.get('resume_hint', 'Resume from the smallest safe slice.')}

## Hard entrypoints
- Repo skill for Codex: `.agents/skills/autorunne-workflow/SKILL.md`
- Repo skill for Claude Code: `.claude/skills/autorunne-workflow/SKILL.md`
- Native Cursor rule: `.cursor/rules/autorunne-workflow.mdc`
- Native Copilot instructions: `.github/copilot-instructions.md`
- Optional wrappers (fallback only):
{wrapper_lines}

## Zero-prompt handoff
Open Codex / Claude Code / Hermes directly in this repo and just give the task. The agent should read `{views_root}/START_HERE.md`, capture a fresh task with `autorunne ingest --source <agent> --task <task>` when needed, then keep write-backs flowing through Autorunne in the background.

## Recommended local commands
{commands_markdown}
"""

    return {
        "PROJECT_CONTEXT.md": project_context,
        "TASKS.md": tasks_md,
        "DECISIONS.md": decisions_md,
        "SESSION_LOG.md": session_log,
        "RULES.md": rules_md,
        "NEXT_ACTION.md": next_action_md,
        "COMMANDS.md": commands_md,
        "START_HERE.md": start_here_md,
    }


def render_agent_compat_bundle() -> dict[str, str]:
    return {
        "autorunne-workflow.md": "# Shared Autorunne Workflow Contract\n\nThis file (`.autorunne/agents/autorunne-workflow.md`) is the shared workflow contract for all supported agents.\n\n- Users should open Codex / Claude Code / Hermes directly and just give the task.\n- Read `.autorunne/views/START_HERE.md` first.\n- Treat `.autorunne/state/*` as the only mutable project state source of truth.\n- Do not edit `.autorunne/state/*` directly; use `autorunne ingest`, `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.\n- If a fresh user task is not recorded yet, capture it with `autorunne ingest --source <agent> --task <task>`.\n- After verified code changes, write progress back through Autorunne so the rendered views stay fresh.\n- Always report changed files, completion status, and the Autorunne commands executed.\n",
        "common.md": "# Common Agent Rules\n\n- Read `.autorunne/agents/autorunne-workflow.md` first.\n- Then read `.autorunne/views/START_HERE.md`.\n- Keep Autorunne in the background; do not ask the user to chat through Autorunne first.\n- Use Autorunne commands to update project state.\n- Keep edits minimal and traceable.\n",
        "claude-code.md": "# Claude Code Adapter\n\n- Start with `.autorunne/agents/autorunne-workflow.md`, then `.autorunne/views/START_HERE.md`.\n- Claude Code should work directly in the repo; wrappers are optional fallback entrypoints.\n- Capture fresh tasks with `autorunne ingest --source claude --task <task>` when needed.\n- Summarize changed files back through `autorunne checkpoint` or `autorunne finish`.\n",
        "codex.md": "# Codex Adapter\n\n- Start with `.autorunne/agents/autorunne-workflow.md`, then `.autorunne/views/START_HERE.md`.\n- Codex should work directly in the repo; wrappers are optional fallback entrypoints.\n- Capture fresh tasks with `autorunne ingest --source codex --task <task>` when needed.\n- Do not edit `.autorunne/state/*` directly.\n",
        "hermes.md": "# Hermes Adapter\n\n- Load `.autorunne/agents/autorunne-workflow.md` first.\n- Then load `.autorunne/views/START_HERE.md`.\n- Hermes should chat directly in the repo while Autorunne stays in the background.\n- Capture fresh tasks with `autorunne ingest --source hermes --task <task>` when needed.\n- Keep project memory synced after each task.\n",
        "cursor.md": "# Cursor Adapter\n\n- Read `.autorunne/agents/autorunne-workflow.md` and `.autorunne/views/START_HERE.md` before agent edits.\n- Keep Cursor changes narrow, validated, and written back through Autorunne.\n- Native repo rule file: `.cursor/rules/autorunne-workflow.mdc`.\n",
        "copilot.md": "# GitHub Copilot Adapter\n\n- Read `.autorunne/agents/autorunne-workflow.md` and `.autorunne/views/START_HERE.md` before edits.\n- Prefer small, testable changes and update Autorunne after each slice.\n- Native repo instructions file: `.github/copilot-instructions.md`.\n",
    }
