# Autorunne State Engine Upgrade Plan

> **For Hermes:** Implement this plan in small verified slices. Keep the current CLI surface stable while moving state truth into `.autorunne/state/*` and rendering `.autorunne/views/*` from it.

**Goal:** Upgrade Autorunne from markdown-first workflow files to a repo-local state engine with rendered views, repo-level skill integrations, and wrapper-based agent entrypoints.

**Architecture:** Keep the current commands (`open/start/checkpoint/finish/sync/doctor/vscode/hooks`) but route them through a new internal state API. Store truth in `.autorunne/state/*`, render `.autorunne/views/*.md`, and add repo-level integration files (`AGENTS.md`, repo skills, wrappers) from templates. Preserve current UX and migrate incrementally.

**Tech Stack:** Python 3.11, Typer CLI, JSON/JSONL state files, pytest.

---

## Phase 1 — State engine foundation

### Task 1: Add failing tests for state bootstrap and render rebuild
**Objective:** Lock the required directory layout and rebuild behavior before implementation.

**Files:**
- Modify: `tests/test_cli.py`
- Create: `tests/test_state_engine.py`

**Checks to add:**
- `autorunne init` creates `.autorunne/state/current.json`, `events.jsonl`, `tasks.json`, `decisions.json`, `sessions.json`
- `autorunne open` in an existing repo creates `.autorunne/views/*`
- deleting `.autorunne/views/START_HERE.md` then running `autorunne render` recreates it from state

### Task 2: Implement state path helpers and core API
**Objective:** Create a single internal API for loading/writing state.

**Files:**
- Modify: `src/autorunne/core/paths.py`
- Create: `src/autorunne/core/state_engine.py`

**Notes:**
- Add helpers for `.autorunne/state`, `.autorunne/views`, `.autorunne/integrations`
- Add functions for bootstrap, load current, append event, rebuild derived indexes, render views from state

### Task 3: Move render targets into views/
**Objective:** Make markdown files generated outputs, not the source of truth.

**Files:**
- Modify: `src/autorunne/core/templater.py`
- Modify: `src/autorunne/core/writer.py`

**Notes:**
- Render markdown into `.autorunne/views/*.md`
- Keep compatibility by ensuring `START_HERE.md` or legacy entry files can still be surfaced if needed

---

## Phase 2 — Command rewiring

### Task 4: Rewire init/adopt/open/sync through state engine
**Objective:** Bootstrap and resume via state, then render views.

**Files:**
- Modify: `src/autorunne/commands/init.py`
- Modify: `src/autorunne/commands/adopt.py`
- Modify: `src/autorunne/commands/open.py`
- Modify: `src/autorunne/commands/sync.py`

**Requirements:**
- emit `workspace_bootstrapped`, `workspace_resumed`, `workspace_synced`
- update `current.json`
- render `.autorunne/views/*`

### Task 5: Rewire start/checkpoint/finish through state engine
**Objective:** Record task lifecycle as events and update derived state.

**Files:**
- Modify: `src/autorunne/commands/start.py`
- Modify: `src/autorunne/commands/checkpoint.py`
- Modify: `src/autorunne/commands/finish.py`

**Requirements:**
- `finish` and `checkpoint` must record changed files, git status, diff stat, validation
- derive `tasks.json`, `decisions.json`, `sessions.json`
- render views after each write

---

## Phase 3 — Integration layer

### Task 6: Add failing tests for integrate + repo skills + wrappers
**Objective:** Define expected integration behavior before implementation.

**Files:**
- Modify: `tests/test_cli.py`
- Create: `tests/test_integrations.py`

**Checks to add:**
- `autorunne integrate --tool all` creates `AGENTS.md`, `.agents/skills/autorunne-workflow/SKILL.md`, `.claude/skills/autorunne-workflow/SKILL.md`
- repo-level integration is installed automatically by `open`
- wrappers `ar-codex`, `ar-claude`, `ar-hermes` are generated for repo scope

### Task 7: Implement integrate command and integration templates
**Objective:** Add explicit and automatic integration materialization.

**Files:**
- Create: `src/autorunne/commands/integrate.py`
- Modify: `src/autorunne/commands/__init__.py`
- Modify: `src/autorunne/cli.py`
- Create: `src/autorunne/core/integrations.py`

**Requirements:**
- support `--tool codex|claude|hermes|all`
- support `--scope repo|user`
- record `integration_installed` / `integration_updated`
- default repo-level install in `open`

### Task 8: Implement wrappers
**Objective:** Make agent entrypoints automatically run `autorunne open` first.

**Files:**
- Create: wrapper templates via `src/autorunne/core/integrations.py`
- Test in `tests/test_integrations.py`

---

## Phase 4 — Observability and doctor

### Task 9: Add record/render/trace/history/show commands
**Objective:** Expose the state engine cleanly to humans, skills, and wrappers.

**Files:**
- Create: `src/autorunne/commands/record.py`
- Create: `src/autorunne/commands/render.py`
- Create: `src/autorunne/commands/trace.py`
- Create: `src/autorunne/commands/history.py`
- Create: `src/autorunne/commands/show.py`
- Modify: `src/autorunne/commands/__init__.py`
- Modify: `src/autorunne/cli.py`

### Task 10: Expand doctor checks
**Objective:** Validate state, views, integrations, wrappers, and freshness.

**Files:**
- Modify: `src/autorunne/commands/doctor.py`
- Modify: `tests/test_cli.py`

**Checks:**
- state files exist
- views exist and can be regenerated
- integrations installed
- wrappers exist for configured scope
- `.autorunne` excluded from export and git tracking

---

## Design decisions to keep implementation lean
- Do **not** introduce a database; use JSON + JSONL only.
- Keep markdown rendering, but move it behind the state engine.
- Keep legacy CLI names; add new commands rather than renaming existing ones.
- Start with repo-level integrations only; user-level can reuse the same renderer/templates.
- Keep `START_HERE.md` as the primary agent entry, but generate repo-local skill files so Codex/Claude can be launched consistently.

## Validation commands
```bash
python -m pytest -q
python -m build
```

## Expected first implementation slice
The best first slice is:
1. state engine bootstrap
2. render command
3. open/init/adopt/sync rewrite
4. one passing test proving state -> views rebuild

That gives the biggest architectural win with the smallest risk.
