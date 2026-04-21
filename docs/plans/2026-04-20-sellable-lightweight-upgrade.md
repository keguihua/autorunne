# Sellable Lightweight Upgrade Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make Autorunne feel strong enough for public sale while staying lightweight, local-first, and terminal-friendly for Codex, Gemini, and Claude Code users.

**Architecture:** Keep the repo-local markdown workflow model, but stop destructive rewrites, strengthen the finish flow, and improve onboarding/install ergonomics. Add only a few high-leverage generated docs (`COMMANDS.md`, `START_HERE.md`) instead of building a platform.

**Tech Stack:** Python 3.11, Typer CLI, pytest, markdown workflow files, lightweight shell installer.

---

### Task 1: Preserve durable memory on re-sync
- Protect manual workflow files from being overwritten on `init`, `adopt`, and `sync`.
- Keep generated files refreshable.
- Verify with tests that `DECISIONS.md` and `TASKS.md` survive `sync`.

### Task 2: Strengthen finish flow
- Add task matching so `finish` can close an existing task instead of only appending a summary.
- Preserve backlog items in `TASKS.md`.
- Optionally append a decision note and touched files to the session log.
- Verify with tests.

### Task 3: Improve agent/window onboarding
- Generate `COMMANDS.md` and `START_HERE.md` with exact instructions for Claude Code, Codex, and Gemini windows.
- Show the next action clearly after `init`/`adopt`.

### Task 4: Improve one-line install story
- Add `scripts/install.sh` for curl-based installation from GitHub.
- Update README and usage docs with the shortest install/start path.

### Task 5: Verify like a product
- Run targeted pytest first, then full suite.
- Run build.
- Run clean smoke tests for installer and CLI in a temp environment.
- Push to GitHub when green.
