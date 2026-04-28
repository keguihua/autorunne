# Changelog

All notable changes to Autorunne are documented here.

## 0.6.16 - 2026-04-28

### Added
- `autorunne status` now prints a user-readable reliability summary with project state, last validation, next step, context-entry readiness, and the visible workflow flow.
- Rendered `.autorunne/views/STATUS.md` and `.autorunne/STATUS.md` as a plain-language project status page for users, students, and clients.

### Improved
- `START_HERE.md` now includes the same user-readable status block so agents and humans can see the current handoff state immediately.
- The project workflow is explained as `open/sync → start/ingest → checkpoint → finish/validate`, making Autorunne's background work visible instead of hidden in state files.

### Verification
- focused status visualization tests
- `python -m pytest -q`
- `python -m build`
- real `course-leads-demo` smoke test planned before release publication

## 0.6.15 - 2026-04-28

### Improved
- Cursor and GitHub Copilot repo instructions now also explicitly tell agents to load the repo Autorunne workflow skill when available.
- This closes the remaining agent-integration gap after 0.6.14: Codex/Claude/Hermes, Cursor, and Copilot all point back to the same repo-local Autorunne workflow instead of relying on the user to say “read Autorunne” each time.

### Documentation
- Refreshed GitHub-facing README install/version/validation sections for `autorunne==0.6.15`.
- Added a dedicated Chinese commercial stability note for early sales, teaching, and delivery positioning.
- Updated product brief, business plan, sales positioning, and 0.6.15 release notes to reflect GitHub Release + PyPI + runtime + real course-demo verification.

### Verification
- `python -m pytest tests/test_integrations.py -q`
- `python -m pytest -q`
- real `course-leads-demo` smoke test with generated repo instructions
- GitHub Release, PyPI wheel/sdist, Hermes runtime venv, and real course-demo smoke test verified for 0.6.15

## 0.6.14 - 2026-04-28

### Added
- Detect lightweight Python teaching/demo repositories even when they have no `pyproject.toml` or `requirements.txt`.
- Infer `python app.py` or `python main.py` as the run command when those entrypoints exist.
- Infer `python -m pytest -q` when a simple Python repo has a `tests/` directory.
- Recognize standard-library HTTP server projects from `http.server` / `ThreadingHTTPServer` signals.

### Improved
- Generated repo skills and agent instructions now explicitly tell agents to load the Autorunne workflow skill automatically instead of waiting for the user to remind them.

### Verification
- `python -m pytest tests/test_scanner.py tests/test_integrations.py -q`
- `python -m pytest -q`
- real `course-leads-demo` smoke test: `autorunne open`, `autorunne sync`, `python -m pytest -q`

## 0.6.13 - 2026-04-28

### Documentation
- refreshed Chinese/English usage guides, product brief, business plan, sales positioning, auto-mode guide, and release playbook around the shipped 0.6.13 multi-package behavior
- added dedicated Chinese 0.6.13 release notes for frontend/backend/contracts monorepo detection and PyPI upgrade guidance

### Fixed
- `autorunne sync` now detects multi-package Node/TypeScript repositories even when the root has no `package.json`.
- First-level package directories such as `frontend`, `backend`, `contracts`, `sdk`, `integrations`, plus `apps/*` and `packages/*`, are scanned for `package.json` files.
- Top-level state is promoted from package details, so monorepos no longer render as `generic` / `unknown` when package data exists.

### Added
- Package-derived commands such as `frontend:build`, `backend:test`, `contracts:compile`, and `contracts:test` render with `cd <package> && npm ...` prefixes.
- Regression coverage for a haopay-style `frontend` / `backend` / `contracts` repository with no root `package.json`.

### Safety
- Single-package Node detection remains on its existing path.
- Sync preserves existing package-derived state instead of overwriting it with `generic` unless the package scan clearly disappears.

### Verification
- `python -m pytest`
- manual haopay-style temporary repo smoke test with `autorunne sync`

## 0.6.12 - 2026-04-28

### Added
- `autorunne update-check` checks PyPI for a newer AutoRunne release and prints an upgrade reminder only.
- `autorunne open` and `autorunne sync` now show a cached daily update reminder when a newer release is available.

### Safety
- AutoRunne still does not silently auto-upgrade by default.
- Update-check cache is stored under `.autorunne/runtime/update_check.json` and does not delete project tasks, state, reports, runtime files, or skills.

### Verification
- `python -m pytest`
- `autorunne version`
- `autorunne update-check --latest-version 9.9.9`
- `autorunne sync`

## 0.6.11 - 2026-04-28

### Improved
- `autorunne self-upgrade --dry-run` now prints the safe pipx command with quoted `--pip-args`, so users can copy and paste it directly.

### Verification
- `python -m pytest`
- `autorunne version`
- `autorunne sync`

## 0.6.10 - 2026-04-28

### Highlights
- Fixed the upgrade path for users who saw `pipx upgrade autorunne` stay on an old cached version even after a newer PyPI release was available.
- Added explicit version commands so users can verify the installed package without relying on pip internals.
- Existing project `.autorunne/` state is preserved during sync/open config migration.

### Added
- `autorunne version` and `autorunne --version` now print the installed package version.
- `autorunne self-upgrade` runs the safe pipx upgrade path using official PyPI and `--no-cache-dir`.
- Chinese operation manual now includes a dedicated “升级 AutoRunne” section.

### Improved
- `scripts/install.sh` now defaults PyPI installs to `--no-cache-dir -i https://pypi.org/simple` to avoid stale caches or mirror lag.
- `autorunne sync` safely migrates old `.autorunne/config.json` files to the running package version while preserving existing tasks, state, reports, runtime files, skills, and rendered views.

### Verification
- `python -m pytest`
- `autorunne version`
- `autorunne sync`

## 0.6.9 - 2026-04-23

### Highlights
- Direct Codex / Claude Code / Hermes use is now the primary product story: users should open the agent in the repo and just give the task, while Autorunne stays in the background.
- Added an agent-neutral ingress command so fresh natural-language tasks can be captured into `.autorunne/` without pretending the user is chatting through Autorunne itself.
- Generated repo instructions now consistently describe wrappers as optional fallback entrypoints instead of the default UX.

### Added
- `src/autorunne/commands/ingest.py`
  - agent-neutral task ingress entrypoint for direct Codex / Claude Code / Hermes sessions
- `autorunne ingest`
  - CLI command for capturing a fresh direct-agent task into workflow state with an explicit `--source`

### Improved
- `src/autorunne/core/state_engine.py`
  - generalized task ingress logging so different agents can record source-specific ingress events like `codex_task_ingressed`
- `src/autorunne/commands/hermes_task.py`
  - now reuses the generic ingress path while staying backward-compatible for Hermes-specific callers
- `src/autorunne/core/integrations.py`
  - repo skill files, Cursor rules, Copilot instructions, and `AGENTS.md` now describe Autorunne as a backend layer and direct agent use as the default
- `src/autorunne/core/templater.py`
  - `START_HERE.md` and adapter docs now tell agents to read the repo state, capture fresh tasks with `autorunne ingest`, and keep wrappers optional
- `README.md`
  - docs now explain the 0.6.9 default workflow in user-facing language

### Verification
- `python -m pytest tests/test_cli.py tests/test_integrations.py -q`
- `python -m pytest -q`
- real repo smoke test: direct `autorunne ingest --source codex ...` into a live repo after `autorunne open`

## 0.6.8 - 2026-04-23

### Highlights
- Autorunne now filters wrapper / integration noise out of automatic change recording, so `.codex`, `.agents`, `.claude`, `.cursor`, `AGENTS.md`, and Copilot scaffolding no longer pollute task history by default.
- Repo wrappers now run an automatic finish pass after a successful agent session, which closes small natural-language tasks without making the user manually run `autorunne finish`.
- Real dogfood on a temp repo confirmed the upgraded flow: Hermes task ingress → `ar-codex` single-file edit → daemon checkpoint → auto-finish with the task moved to completed.

### Added
- `src/autorunne/commands/auto_finish.py`
  - wrapper-friendly command for automatically closing the active task when a successful agent run leaves meaningful repo changes behind
- `WorkflowConfig.auto_record_ignored_paths`
  - dedicated config list for ignoring wrapper / integration noise during automatic recording

### Improved
- `src/autorunne/core/auto_record.py`
  - now filters non-user-facing integration noise before creating automatic tasks / checkpoints
  - now supports wrapper-driven auto-finish with doc-only validation shortcuts and a cleaner generic next action after completion
- `src/autorunne/commands/daemon.py`
  - now skips auto-sync / auto-record work when only ignored noise files changed
- `src/autorunne/core/integrations.py`
  - generated wrappers now invoke `autorunne auto-finish --source <agent>` after successful agent execution
- repo dogfood behavior
  - finish summaries now focus on meaningful changed files instead of listing wrapper bootstrap artifacts

### Verification
- `python -m pytest -q`
- `python -m build`
- real temp-repo dogfood with:
  - `autorunne open`
  - `autorunne hermes-task`
  - `./.autorunne/bin/ar-codex exec --full-auto ...`
  - verified `TASKS.md`, `NEXT_ACTION.md`, and `SESSION_LOG.md` auto-updated with a completed task and filtered file list

### Release assets
- `autorunne-0.6.8-py3-none-any.whl`
- `autorunne-0.6.8.tar.gz`

## 0.6.7 - 2026-04-23

### Highlights
- Generated Codex and Claude repo skill files now include valid YAML frontmatter, fixing the `missing YAML frontmatter delimited by ---` warning when opening a repo through `ar-codex`.
- Generated Cursor rule metadata is now cleaner so all shipped agent-side integration files use safer, more consistent formats.
- Autorunne keeps the 0.6.6 runtime-managed auto-recording flow while making the repo entry experience more reliable across agents.

### Improved
- `src/autorunne/core/integrations.py`
  - repo skill files under `.agents/skills/autorunne-workflow/` and `.claude/skills/autorunne-workflow/` now render with valid YAML frontmatter
  - Cursor rule output no longer emits an empty `globs:` frontmatter key
- generated repo integrations
  - Codex / Claude / Hermes / Cursor / Copilot entry files are now easier to dogfood as a group without format warnings masking real problems

### Verification
- `python -m pytest tests/test_integrations.py -q`
- `python -m pytest tests/test_cli.py tests/test_install_script.py -q`
- `python -m pytest -q`
- generated a fresh demo repo and inspected `.agents/skills/autorunne-workflow/SKILL.md`, `.claude/skills/autorunne-workflow/SKILL.md`, `.cursor/rules/autorunne-workflow.mdc`, and `.github/copilot-instructions.md`

### Release assets
- `autorunne-0.6.7-py3-none-any.whl`
- `autorunne-0.6.7.tar.gz`

## 0.6.6 - 2026-04-23

### Highlights
- Autorunne now auto-records local file changes into workflow state as soon as the watcher / daemon sees real repo edits.
- Repo wrappers (`ar-codex`, `ar-claude`, `ar-hermes`) now start a background daemon automatically so users can just enter the repo and keep coding.
- The first detected local change auto-opens a focused task lane, and later changes in the same slice append checkpoint-style progress without asking the user to manage `start` / `checkpoint` manually.

### Added
- `src/autorunne/core/auto_record.py`
  - shared change-tracking helper that turns detected file edits into automatic task + checkpoint write-backs
- default config flag `auto_record_on_change = true`
  - keeps automatic change recording enabled for existing and newly initialized workspaces

### Improved
- `autorunne watch`
  - now records change-driven progress, not only sync output
  - reports how many automatic records were written plus the latest summary
- `autorunne daemon`
  - now auto-records detected changes into `.autorunne/state/*`
  - returns the latest changed files and latest auto-record summary in CLI output
- repo wrapper scripts
  - now spawn a bounded background daemon automatically unless explicitly disabled
  - preserve the child command exit code while cleaning up the daemon on exit

### Docs and positioning
- Updated README, usage docs, operator manual, auto-mode explainer, release playbook, and install examples to `0.6.6`
- Added 0.6.6 release notes focused on automatic change-driven workflow recording

### Verification
- `python -m pytest tests/test_cli.py -q`
- `python -m pytest tests/test_install_script.py -q`
- `python -m build`

### Release assets
- `autorunne-0.6.6-py3-none-any.whl`
- `autorunne-0.6.6.tar.gz`

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
