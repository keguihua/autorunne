# Autorunne Copilot Instructions

This repository uses Autorunne as the backend workflow and project-memory layer.

Required behavior:
1. The user should be able to open Copilot or its agent mode directly and just give the task.
2. When this repo skill is available, load this repo skill as the workflow source of truth and follow it automatically.
3. Do not wait for the user to remind you to read Autorunne, START_HERE, or the workflow files.
4. Read `.autorunne/views/START_HERE.md` first.
5. Treat `.autorunne/state/*` as the only mutable project state source of truth.
6. Do not edit `.autorunne/state/*` directly.
7. If a fresh user task is not recorded yet, capture it with `autorunne ingest --source copilot --task <task>`.
8. Use `autorunne checkpoint` for meaningful partial progress.
9. Use `autorunne finish` after verification is complete.
10. Include changed files, completion status, and Autorunne commands in the final report.
