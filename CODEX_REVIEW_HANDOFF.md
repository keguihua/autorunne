# CODEX_REVIEW_HANDOFF.md

## Status

COMPLETE

## Workspace

- Worktree: `/Users/huafire777/.config/superpowers/worktrees/autorunne/grok-autorunne-0.6.34-reliability`
- Branch: `grok/autorunne-0.6.34-reliability`
- Repair base SHA: `dae2d6ea3b337a23e68083cfa81333a820bc3cee`
- Earlier 0.6.33 baseline: `f1828d4cea433a0337c997892fa10b29544581d5` via `a7debe1465ab902f0c6ffd1ac8c6916420322512`
- Confirm final HEAD with `git rev-parse HEAD` in the worktree; do not treat a SHA written inside this file as self-describing.

Original checkout `/Users/huafire777/Desktop/program/autorunne` was left on `main`. All edits were in the specified worktree.

## Changed files (this repair)

| File | Purpose |
| --- | --- |
| `src/autorunne/core/persistence.py` | JSONL newline-terminated fail-closed; lock timeout covers thread gate + OS lock |
| `src/autorunne/core/memory.py` | Pending-compaction journal so retries keep the original batch id |
| `tests/test_persistence.py` | Regression tests for JSONL tail rules and thread timeout |
| `tests/test_memory_commands.py` | Crash-after-session-save compact idempotency + new-batch-after-retry |
| `CHANGELOG.md` | Record the three Codex-reproduced fixes |
| `docs/Autorunne-Release-Notes-0.6.34-ZH.md` | Candidate notes match the repaired behavior |
| `CODEX_REVIEW_HANDOFF.md` | This review package |

`git diff --name-only dae2d6ea3b337a23e68083cfa81333a820bc3cee..HEAD` before the documentation commit was only:

```text
src/autorunne/core/memory.py
src/autorunne/core/persistence.py
tests/test_memory_commands.py
tests/test_persistence.py
```

## Fixes

### 1. JSONL newline-terminated bad final record

**Cause:** `_parse_jsonl()` used `str.splitlines()`, which drops the trailing newline, so `{bad}\n` looked like an incomplete last line and was deleted.

**Fix:** Repair only when the last fragment is malformed **and** the file does not end with `\n`. A newline-terminated bad record raises `StateCorruptionError` and leaves original bytes unchanged. Middle-line corruption still fails closed.

### 2. Same-process thread lock timeout

**Cause:** `state.gate.acquire()` blocked forever. `timeout` only applied to the later OS file lock.

**Fix:** One deadline covers both stages. The thread `RLock` is acquired with the remaining time; the OS lock polls until the same deadline. Nested same-thread acquires still succeed immediately. Timeout raises `StateLockTimeoutError` with the repo path and `Wait for the other command to finish, then retry.` OS handle is closed if the file lock times out.

### 3. Compact retry after partial commit

**Cause:** Batch ids were recomputed from live state. After archive + `save_workspace_state()`, sessions were trimmed but events were not, so a retry produced a new batch id and duplicated archived events.

**Fix:** Before mutating archive/state/events, persist `.autorunne/runtime/pending-compaction.json` with the original batches, kept sessions, and kept events. Retry applies that journal. Archive merge stays idempotent by marker. A later compact with new data still appends a new batch. No SQLite/database.

## RED / GREEN evidence

Commands used `AUTORUNNE_DISABLE_UPDATE_CHECK=1` and worktree `.venv`.

| Test | RED | GREEN |
| --- | --- | --- |
| `test_jsonl_newline_terminated_bad_final_record_fails_closed` | `DID NOT RAISE StateCorruptionError` | pass with sibling JSONL tests |
| `test_jsonl_incomplete_final_fragment_without_newline_is_repaired` | already passed against interrupt-without-newline | pass |
| `test_workspace_lock_times_out_while_other_thread_holds_it` | `AssertionError: waiter entered the critical section` after ~2.03s | pass (`11 passed` persistence) |
| `test_compact_retry_after_event_rewrite_crash_is_idempotent` | `assert 2 == 1` batch markers | pass |
| `test_compact_after_crash_retry_still_appends_a_new_batch` | `assert 3 == 2` batch markers | pass |
| `test_archive_batch_write_is_idempotent` | stayed green (archive-then-save crash) | pass |

Persistence after issues 1–2: `11 passed in 1.04s`.  
Memory after issue 3: `10 passed in 1.41s`.

## Verification commands

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
- Output: `45 passed in 7.16s`

### Full

```bash
AUTORUNNE_DISABLE_UPDATE_CHECK=1 PATH="$PWD/.venv/bin:$PATH" \
.venv/bin/python -m pytest --override-ini addopts= -q
```

- Exit code: 0
- Output: `132 passed in 21.02s`

### Hygiene

```bash
git diff --check
```

- Exit code: 0

### Build

```bash
.venv/bin/python -m build
```

- Exit code: 0
- Output: `Successfully built autorunne-0.6.34.tar.gz and autorunne-0.6.34-py3-none-any.whl`

### Metadata

```bash
unzip -p dist/autorunne-0.6.34-py3-none-any.whl \
  'autorunne-0.6.34.dist-info/METADATA' | sed -n '1,8p'
```

- Exit code: 0
- Contains `Name: autorunne` and `Version: 0.6.34`

### Fresh venv wheel install

Created a new temporary venv with Python 3.11, installed `dist/autorunne-0.6.34-py3-none-any.whl` plus dependencies, then ran `autorunne --version`.

- pip exit code: 0
- CLI output: `AutoRunne 0.6.34`
- Temporary venv was deleted afterwards; worktree `.venv` was not replaced.

## Fault injection results

- Archive written, `save_workspace_state` fails, retry: one batch marker; `test session 0` and `event 0` once.
- `save_workspace_state` succeeds, `_write_events` fails, retry: one batch marker; `test session 0`, `event 0`, `event 1` once.
- After that recovered compact, adding six new January records and compacting again: exactly two batch markers; old and new session/event titles each appear once.

## Remaining risk

- Windows `msvcrt.locking` still not executed on Windows.
- JSON recovery remains per-file, not a multi-file snapshot.
- Pending-compaction journal is local JSON only; a hand-edited corrupt journal is treated as absent if it has no `batches`.

## Publication

- GitHub push = NOT PERFORMED
- GitHub tag = NOT PERFORMED
- GitHub Release = NOT PERFORMED
- PyPI upload = NOT PERFORMED
- GitHub Discussions = NOT PERFORMED
- merge to `main` = NOT PERFORMED

Please independently re-run focused tests, full suite, build, and a fresh-venv `autorunne --version` on this branch. Do not merge or publish without explicit user authorization.
