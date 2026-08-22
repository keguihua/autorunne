# CODEX_REVIEW_HANDOFF.md

## Status

COMPLETE

## Workspace

- Worktree: `/Users/huafire777/.config/superpowers/worktrees/autorunne/grok-autorunne-0.6.34-reliability`
- Branch: `grok/autorunne-0.6.34-reliability`
- Repair base SHA: `c2ed45b316e008ff9d18d5b800f8fec1f5d4c72a`
- Confirm final HEAD with `git rev-parse HEAD` in the worktree. Do not treat a SHA inside this file as self-describing.

Original checkout `/Users/huafire777/Desktop/program/autorunne` stayed on `main`. All edits were in the specified worktree. No rebase, reset, or rewrite of earlier commits.

## Changed files

| File | Purpose |
| --- | --- |
| `src/autorunne/core/mutation.py` | Central `state_mutator` gate: lock, recover pending compact, then mutate |
| `src/autorunne/core/memory.py` | `recover_pending_compaction()` with fail-closed error wrapping |
| `src/autorunne/core/state_engine.py` | Public mutators use `state_mutator` instead of lock-only |
| `tests/test_memory_commands.py` | Post-crash record/start/fail-closed/new-compact regressions |
| `CHANGELOG.md` | Record the recover-before-mutate fix |
| `docs/Autorunne-Release-Notes-0.6.34-ZH.md` | Candidate notes match the repaired gate |
| `CODEX_REVIEW_HANDOFF.md` | This review package; trailing whitespace removed |

Primitives `load_workspace_state`, `save_workspace_state`, `append_event`, `load_events`, and `render_views` stay lock-only so `_apply_compaction_plan()` cannot recurse.

## How pending recovery runs before new mutation

1. `state_mutator` acquires the re-entrant workspace lock.
2. It lazy-imports `recover_pending_compaction` (avoids `memory` / `state_engine` import cycles).
3. If `.autorunne/runtime/pending-compaction.json` exists, recovery finishes the original batch and deletes the journal.
4. Only then does `record` / `start` / `checkpoint` / `finish` / ingest / task mutation / `sync` / `bootstrap` run.
5. If recovery fails, `RuntimeError` names the previous compact, the journal stays, and the user mutator does not write.

`compact_memory()` still applies an existing journal on retry and does not start a second compact in that same call.

## RED / GREEN evidence

Commands used `AUTORUNNE_DISABLE_UPDATE_CHECK=1` and the worktree `.venv`.

RED on `c2ed45b` implementation (tests added, product code unchanged):

```bash
.venv/bin/python -m pytest \
  tests/test_memory_commands.py::test_pending_compaction_recovers_before_new_manual_record \
  tests/test_memory_commands.py::test_pending_compaction_recovers_before_new_start \
  tests/test_memory_commands.py::test_failed_pending_recovery_blocks_new_state_mutation \
  tests/test_memory_commands.py::test_pending_recovery_then_new_compact_appends_one_batch \
  --override-ini addopts= -q
```

- Exit code: 1
- `test_pending_compaction_recovers_before_new_manual_record`: `assert 0 == 1` for `"record created after crash"` after compact applied the old plan
- `test_pending_compaction_recovers_before_new_start`: `assert 0 == 1` for `"task after crash"`
- `test_failed_pending_recovery_blocks_new_state_mutation`: `assert 0 == 1` (`record` exit_code was 0; mutator wrote without recovering)
- `test_pending_recovery_then_new_compact_appends_one_batch`: `assert 0 == 1` for the post-crash record after a later compact

GREEN after the gate:

```bash
.venv/bin/python -m pytest tests/test_memory_commands.py --override-ini addopts= -q
```

- Exit code: 0
- `14 passed` (the four new tests plus prior compact crash tests)

## Verification

### Focused

```bash
AUTORUNNE_DISABLE_UPDATE_CHECK=1 PATH="$PWD/.venv/bin:$PATH" \
.venv/bin/python -m pytest \
  tests/test_persistence.py \
  tests/test_memory_commands.py \
  tests/test_state_engine.py \
  tests/test_update_check.py \
  --override-ini addopts= -q
```

- Exit code: 0
- Output: `49 passed in 6.71s`

### Full

```bash
AUTORUNNE_DISABLE_UPDATE_CHECK=1 PATH="$PWD/.venv/bin:$PATH" \
.venv/bin/python -m pytest --override-ini addopts= -q
```

- Exit code: 0
- Output: `136 passed in 19.68s`

### Hygiene

`git diff --check` on the recovery-gate commit: exit 0.

`git diff --check c2ed45b316e008ff9d18d5b800f8fec1f5d4c72a..HEAD` after that commit: exit 0.

The previous handoff line `Persistence after issues 1–2: ...` had trailing whitespace. That line is removed in this rewrite. Re-run `git diff --check` and the range check after the documentation commit and record the real exit codes there.

### Build / metadata / fresh venv

Re-run after the documentation commit. Expected unchanged: wheel `Name: autorunne`, `Version: 0.6.34`, fresh venv `AutoRunne 0.6.34`.

## Remaining risk

- Windows `msvcrt.locking` still not executed on Windows.
- JSON recovery remains per-file, not a multi-file snapshot.
- Direct calls to `save_workspace_state` / `append_event` bypass the mutator gate by design, because compact recovery uses those primitives.

## Publication

- GitHub push = NOT PERFORMED
- GitHub tag = NOT PERFORMED
- GitHub Release = NOT PERFORMED
- PyPI upload = NOT PERFORMED
- GitHub Discussions = NOT PERFORMED
- merge to `main` = NOT PERFORMED
