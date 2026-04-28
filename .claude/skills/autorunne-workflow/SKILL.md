---
name: autorunne-workflow
description: Repo-local Autorunne workflow instructions for this repository
version: 0.6.15
---

# Autorunne Workflow Skill

## Purpose
This repository uses Autorunne as the backend workflow and project-memory layer.

## User-facing rule
The user should be able to open Claude Code directly, talk naturally, and let Autorunne maintain state in the background. Do not ask the user to chat through Autorunne first.

## Skill-first rule for agents
When this repo skill is available, load this repo skill as the workflow source of truth and follow it automatically. Do not wait for the user to remind you to read Autorunne, START_HERE, or the workflow files.

## Required startup flow
1. Read `.autorunne/views/START_HERE.md`.
2. Treat `.autorunne/state/*` as the only project state source of truth.
3. Never write `.autorunne/state/*` directly. Use `autorunne ingest`, `autorunne start`, `autorunne checkpoint`, `autorunne finish`, or `autorunne sync`.
4. If the user gives a fresh natural-language task and no matching active task is recorded yet, capture it with `autorunne ingest --source claude --task <task>`.
5. Before beginning a new implementation slice, run `autorunne open` if the workspace has not been resumed yet in this session.
6. After meaningful verified progress, write back through Autorunne so the rendered views stay fresh.
7. Prefer the wrapper `./.autorunne/bin/ar-claude` only as an optional hard-entry fallback, not as the default requirement you impose on the user.

## Read order
1. `.autorunne/views/START_HERE.md`
2. `.autorunne/views/PROJECT_CONTEXT.md`
3. `.autorunne/views/TASKS.md`
4. `.autorunne/views/DECISIONS.md`
5. `.autorunne/views/NEXT_ACTION.md`
