# AGENTS

Short instruction layer for this repo:
1. Users should open Codex / Claude Code / Hermes directly and just give the task.
2. Read `.autorunne/views/START_HERE.md` first.
3. Use repo skill files under `.agents/skills/autorunne-workflow/` or `.claude/skills/autorunne-workflow/`.
4. Cursor should use `.cursor/rules/autorunne-workflow.mdc` when present.
5. GitHub Copilot should use `.github/copilot-instructions.md` when present.
6. Do not write `.autorunne/state/*` directly.
7. If a fresh task is not recorded yet, capture it with `autorunne ingest --source <agent> --task <task>`.
8. Wrappers like `./.autorunne/bin/ar-codex`, `./.autorunne/bin/ar-claude`, or `./.autorunne/bin/ar-hermes` are optional fallback entrypoints, not the required default UX.
