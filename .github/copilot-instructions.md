# Autorunne Copilot Instructions

This repository uses Autorunne as the backend workflow and project-memory layer.

Required behavior:
1. The user should be able to open Copilot or its agent mode directly and just give the task.
2. Read `.autorunne/views/START_HERE.md` first.
3. Treat `.autorunne/state/*` as the only mutable project state source of truth.
4. Do not edit `.autorunne/state/*` directly.
5. If a fresh user task is not recorded yet, capture it with `autorunne ingest --source copilot --task <task>`.
6. Use `autorunne checkpoint` for meaningful partial progress.
7. Use `autorunne finish` after verification is complete.
8. Include changed files, completion status, and Autorunne commands in the final report.
