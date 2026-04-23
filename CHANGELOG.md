# Changelog

All notable changes to Autorunne are documented here.

## 0.6.5 - 2026-04-23

### Highlights
- Autorunne now keeps `in-progress` as a single-focus lane and automatically demotes stale unfinished work back into `Next up`.
- Outdated release backlog items for older shipped versions now move into an explicit `Archived / historical` section instead of polluting the live queue.
- Real dogfooding on the `autorunne` repo confirmed the tighter task board behavior with `start`, `checkpoint`, `finish`, and explicit `task` commands.

### Added
- `TASKS.md -> Archived / historical` rendered section for older backlog that should stay visible without distracting from the current roadmap
- automatic release-backlog archiving for stale items like old tag / publish / PyPI tasks tied to versions behind the current shipped version

### Improved
- `start`, `checkpoint`, `finish`, and `sync` now realign focus so only the current active task stays in `In progress`
- stale `in-progress` items are demoted into `Next up` instead of lingering as fake active work
- `autorunne task add --section in-progress` now sets the active task, and `task done` / `task remove` realign focus afterwards
- `autorunne status` now reports archived backlog counts as part of task counts

### Docs and positioning
- Updated README, usage docs, operator manual, release playbook, and versioned install examples to `0.6.5`
- Added 0.6.5 release notes covering release-backlog archiving and focus-lane cleanup

### Verification
- `python -m pytest tests/test_cli.py -q`
- `python -m pytest -q`
- real-project workflow verified on the `autorunne` repo itself with:
  - `task add --section in-progress`
  - `start`
  - `checkpoint --validate "python -m pytest -q"`
  - `finish --validate "python -m pytest -q"`
  - `task remove --section next-up`

### Release assets
- `autorunne-0.6.5-py3-none-any.whl`
- `autorunne-0.6.5.tar.gz`

## 0.6.4 - 2026-04-22

### Highlights
- Autorunne now installs a stronger **cross-agent workflow contract** so Hermes, Codex, Claude Code, Cursor, and GitHub Copilot can all enter the same repo-local workflow.
- Repo integrations now include native agent instruction files for Cursor and GitHub Copilot, not only repo skills and wrappers for Codex / Claude / Hermes.
- Rendered onboarding docs now point every supported agent back to the shared workflow contract before coding.

### Added
- `.autorunne/agents/autorunne-workflow.md`
  - shared repo-local workflow contract for all supported agents
  - requires `autorunne start` / `autorunne checkpoint` / `autorunne finish` instead of direct state edits
- Cursor native integration
  - installs `.cursor/rules/autorunne-workflow.mdc`
- GitHub Copilot native integration
  - installs `.github/copilot-instructions.md`

### Improved
- `autorunne integrate --tool all`
  - now installs Cursor and Copilot repo integrations in addition to Codex / Claude / Hermes support
- rendered `START_HERE.md`
  - now points agents at `.autorunne/agents/autorunne-workflow.md` first
  - explicitly lists native Cursor and Copilot integration files alongside repo skills and wrappers
- rendered agent adapter docs
  - common, Codex, Claude Code, Hermes, Cursor, and Copilot adapters now all point at the same shared workflow contract
- `autorunne doctor`
  - now checks the complete repo-level agent integration set, including Cursor and Copilot files
- CLI onboarding output
  - now advertises Cursor / Copilot / Hermes alongside Claude Code / Codex / Gemini

### Docs and positioning
- Updated README and install/version references to `0.6.4`
- Added 0.6.4 release notes and refreshed release examples to match the new version
- Kept the product positioning aligned with Autorunne as a workflow + agent-adapter layer rather than a single-agent wrapper

### Verification
- `python -m pytest tests/test_integrations.py tests/test_cli.py tests/test_phase4_commands.py -q`
- `python -m build`
- real install/release references updated to `0.6.4`

### Release assets
- `autorunne-0.6.4-py3-none-any.whl`
- `autorunne-0.6.4.tar.gz`

## 0.6.3 - 2026-04-21

### Highlights
- Autorunne is now a more complete **state-workflow CLI** for real project delivery, not just a markdown-first repo helper.
- Existing markdown-only `.autorunne/*.md` workspaces can now be upgraded cleanly into the state engine.
- Repo status and task management now reflect real workflow state instead of relying only on fresh repo scans.

### Added
- `autorunne migrate`
  - imports older markdown-only workspaces into `.autorunne/state/*`
  - rebuilds `.autorunne/views/*`
  - preserves next action and legacy task context during upgrade
- `autorunne task add`
- `autorunne task done`
- `autorunne task remove`

### Improved
- `autorunne status`
  - now prefers state-backed workflow truth
  - shows active task, last action, task counts, session/event counts, integrations, and wrappers
  - clearly flags legacy workspaces that need migration
- `autorunne doctor`
  - checks legacy migration state in addition to state files, views, snapshot, integrations, wrappers, and rebuildability
- `autorunne show`, `autorunne history`, `autorunne trace`
  - now guide the user to run `autorunne migrate` first when the repo still uses a legacy markdown-only workspace
- scanner resume hints
  - lowers the weight of editor noise like `.vscode/`
  - improves dirty-file prioritization for real work files
- package/module loading
  - `src/autorunne/__init__.py` now uses lazy app loading to avoid CLI import side effects

### Docs and positioning
- Updated README and install/version references to `0.6.3`
- Updated Chinese and English usage docs to match the real CLI surface
- Updated product brief, business plan, and sales positioning docs so external messaging matches the shipped 0.6.3 behavior

### Verification
- `pytest -q`
- `python -m build`
- real-project workflow verified on the `autorunne` repo itself:
  - `status`
  - `migrate`
  - `open --with-vscode`
  - `start`
  - `checkpoint --validate "pytest -q"`
  - `finish --validate "pytest -q"`
  - `show`
  - `history`
  - `trace`
  - `doctor`

### Release assets
- `autorunne-0.6.3-py3-none-any.whl`
- `autorunne-0.6.3.tar.gz`

## 0.6.2 - 2026-04-21

### Highlights
- moved Autorunne to a state-first workflow architecture
- introduced `.autorunne/state/*` as the source of truth
- rendered `.autorunne/views/*` from state
- added repo-level integrations and wrappers

## 0.6.1 - 2026-04-21

### Highlights
- published Autorunne to PyPI
- stabilized public install and release flow

## 0.6.0 - 2026-04-21

### Highlights
- release prep and public packaging groundwork
