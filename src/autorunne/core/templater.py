from __future__ import annotations

from datetime import datetime, timezone
from typing import Iterable

from autorunne.core.paths import WORKFLOW_DIR


TEMPLATES = {
    "PROJECT_CONTEXT.md": """# Project Context\n\n## Project\n- Name: {repo_name}\n- Stack: {stack}\n- Framework: {framework}\n- Package manager: {package_manager}\n\n## Important files\n{important_files}\n\n## Important directories\n{source_dirs}\n\n## Current state\n- Workflow initialized by Autorunne\n- Repository type inferred from local scan\n- Confirm assumptions below before large changes\n\n## Constraints\n- Keep changes scoped to the current task\n- Do not commit `{workflow_dir}` to the public repo\n- Verify run/test commands before refactoring\n\n## Manual confirmation needed\n- Confirm the main runtime command\n- Confirm the test command\n- Confirm which modules are stable vs risky\n""",
    "TASKS.md": """# Tasks\n\n## Completed / inferred\n{completed}\n\n## In progress\n- [ ] Validate local run and test commands\n\n## Next up\n- [ ] {next_action}\n\n## Known unknowns\n- [ ] Confirm deployment flow\n- [ ] Confirm protected or high-risk modules before large edits\n""",
    "DECISIONS.md": """# Decisions\n\n## Baseline assumptions\n- Project detected as: {stack}\n- Main framework likely: {framework}\n- Package manager likely: {package_manager}\n\n## Pending confirmations\n- Confirm whether these detections are correct\n- Record important architectural decisions here before large changes\n\n## Recorded decisions\n- Add durable project decisions here as they are confirmed.\n""",
    "SESSION_LOG.md": """# Session Log\n\n## {timestamp} | workflow initialized\n- Mode: {mode}\n- Repo: {repo_name}\n- Stack: {stack}\n- Framework: {framework}\n- Next action: {next_action}\n""",
    "RULES.md": """# Rules\n\n1. Read `PROJECT_CONTEXT.md`, `TASKS.md`, and the latest `SESSION_LOG.md` before coding.\n2. Only change files related to the current task.\n3. Prefer the smallest safe change over broad refactors.\n4. Run the relevant validation command after each meaningful change.\n5. Update workflow docs after finishing a task.\n6. Keep `{workflow_dir}` local-only.\n""",
    "NEXT_ACTION.md": """# Next Action\n\n{next_action}\n""",
    "COMMANDS.md": """# Commands\n\n## Detected local commands\n{commands_markdown}\n\n## Suggested daily loop\n1. Open `START_HERE.md` in your agent window.\n2. Do the smallest safe change.\n3. Run the most relevant local validation command above.\n4. Run `autorunne finish --summary \"what you finished\" --next \"next concrete step\"`.\n""",
    "START_HERE.md": """# Start Here\n\nAutorunne is built to work with **Claude Code**, **Codex**, **Gemini**, **Hermes**, **Cursor**, and **GitHub Copilot** in a normal repo folder or VS Code terminal.\n\n## Read these files first\n- `PROJECT_CONTEXT.md`\n- `TASKS.md`\n- `DECISIONS.md`\n- `NEXT_ACTION.md`\n- `COMMANDS.md`\n\n## Current focus\n- Next action: {next_action}\n- Stack: {stack}\n- Framework: {framework}\n\n## Suggested prompt for any coding agent window\n```text\nUse `.autorunne/` as the source of truth for this repo. Read PROJECT_CONTEXT.md, TASKS.md, DECISIONS.md, NEXT_ACTION.md, and COMMANDS.md before coding. Then continue with the current next action: {next_action}\n```\n\n## Recommended local commands\n{commands_markdown}\n""",
}

AGENT_TEMPLATES = {
    "common.md": """# Common Agent Rules\n\n- Read the shared workflow files before changing code.\n- Ask for clarification when a risky change is unclear.\n- Keep edits minimal and traceable.\n- Update task and session state after work is done.\n""",
    "claude-code.md": """# Claude Code Adapter\n\n- Start with the shared workflow files under `.autorunne/`.\n- Explain planned scope before broad edits.\n- Prefer small patches over rewrites.\n""",
    "codex.md": """# Codex Adapter\n\n- Use the shared workflow files as the single source of truth.\n- Avoid opportunistic refactors unless explicitly requested.\n- After coding, summarize changed files and update workflow docs.\n""",
    "hermes.md": """# Hermes Adapter\n\n- Load project context from `.autorunne/` first.\n- Use the next action as the default starting point.\n- Keep project memory synced after each task.\n""",
    "cursor.md": """# Cursor Adapter\n\n- Read shared workflow docs before agent edits.\n- Keep changes narrow and validate locally.\n- Reflect completed work back into `.autorunne/`.\n""",
    "copilot.md": """# GitHub Copilot Adapter\n\n- Use `.autorunne/START_HERE.md` as the fastest entry point.\n- Read the shared workflow docs before generating or editing code.\n- Prefer small, testable changes and update `checkpoint` or `finish` after each meaningful slice.\n""",
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
        ], "Initial scan complete"),
        "next_action": scan["next_action"],
        "mode": mode,
        "timestamp": timestamp,
        "workflow_dir": WORKFLOW_DIR,
        "commands_markdown": _render_commands(scan),
    }
    rendered = {name: template.format(**context) for name, template in TEMPLATES.items()}
    rendered.update({f"agents/{name}": template for name, template in AGENT_TEMPLATES.items()})
    return rendered
