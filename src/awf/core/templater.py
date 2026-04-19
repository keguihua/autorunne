from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from awf.core.paths import WORKFLOW_DIR


TEMPLATES = {
    "PROJECT_CONTEXT.md": """# Project Context\n\n## Project\n- Name: {repo_name}\n- Stack: {stack}\n- Framework: {framework}\n- Package manager: {package_manager}\n\n## Important files\n{important_files}\n\n## Important directories\n{source_dirs}\n\n## Current state\n- Workflow initialized by AI Workflow CLI\n- Repository type inferred from local scan\n- Confirm assumptions below before large changes\n\n## Constraints\n- Keep changes scoped to the current task\n- Do not commit `{workflow_dir}` to the public repo\n- Verify run/test commands before refactoring\n\n## Manual confirmation needed\n- Confirm the main runtime command\n- Confirm the test command\n- Confirm which modules are stable vs risky\n""",
    "TASKS.md": """# Tasks\n\n## Completed / inferred\n{completed}\n\n## In progress\n- [ ] Validate local run and test commands\n\n## Next up\n- [ ] {next_action}\n\n## Known unknowns\n- [ ] Confirm deployment flow\n- [ ] Confirm protected or high-risk modules before large edits\n""",
    "DECISIONS.md": """# Decisions\n\n## Baseline assumptions\n- Project detected as: {stack}\n- Main framework likely: {framework}\n- Package manager likely: {package_manager}\n\n## Pending confirmations\n- Confirm whether these detections are correct\n- Record important architectural decisions here before large changes\n""",
    "SESSION_LOG.md": """# Session Log\n\n## {timestamp} | workflow initialized\n- Mode: {mode}\n- Repo: {repo_name}\n- Stack: {stack}\n- Framework: {framework}\n- Next action: {next_action}\n""",
    "RULES.md": """# Rules\n\n1. Read `PROJECT_CONTEXT.md`, `TASKS.md`, and the latest `SESSION_LOG.md` before coding.\n2. Only change files related to the current task.\n3. Prefer the smallest safe change over broad refactors.\n4. Run the relevant validation command after each meaningful change.\n5. Update workflow docs after finishing a task.\n6. Keep `{workflow_dir}` local-only.\n""",
    "NEXT_ACTION.md": """# Next Action\n\n{next_action}\n""",
}

AGENT_TEMPLATES = {
    "common.md": """# Common Agent Rules\n\n- Read the shared workflow files before changing code.\n- Ask for clarification when a risky change is unclear.\n- Keep edits minimal and traceable.\n- Update task and session state after work is done.\n""",
    "claude-code.md": """# Claude Code Adapter\n\n- Start with the shared workflow files under `.ai-workflow/`.\n- Explain planned scope before broad edits.\n- Prefer small patches over rewrites.\n""",
    "codex.md": """# Codex Adapter\n\n- Use the shared workflow files as the single source of truth.\n- Avoid opportunistic refactors unless explicitly requested.\n- After coding, summarize changed files and update workflow docs.\n""",
    "hermes.md": """# Hermes Adapter\n\n- Load project context from `.ai-workflow/` first.\n- Use the next action as the default starting point.\n- Keep project memory synced after each task.\n""",
    "cursor.md": """# Cursor Adapter\n\n- Read shared workflow docs before agent edits.\n- Keep changes narrow and validate locally.\n- Reflect completed work back into `.ai-workflow/`.\n""",
}


def _bulletize(items: Iterable[str], default: str) -> str:
    values = list(items)
    if not values:
        values = [default]
    return "\n".join(f"- {item}" for item in values)


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
    }
    rendered = {name: template.format(**context) for name, template in TEMPLATES.items()}
    rendered.update({f"agents/{name}": template for name, template in AGENT_TEMPLATES.items()})
    return rendered
