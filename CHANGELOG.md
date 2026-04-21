# Changelog

All notable changes to Autorunne are documented here.

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
