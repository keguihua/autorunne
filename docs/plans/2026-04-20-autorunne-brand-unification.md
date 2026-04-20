# Autorunne Brand Unification Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Make the Autorunne repo consistently use the Autorunne brand across package metadata, install surfaces, CLI/docs, local workflow directory, and business-facing materials.

**Architecture:** Keep the product centered on a primary `autorunne` package/CLI while preserving as little legacy naming as possible. Update code, tests, docs, and release metadata together so install/build/readme/business docs all tell the same story.

**Tech Stack:** Python 3.11, Typer, setuptools, pytest, Markdown docs.

---

### Task 1: Rebrand the package and workflow root
- Rename the Python package/import path from `autorunne` to `autorunne`
- Change the default workflow directory from `.autorunne` to `.autorunne`
- Change CLI/help strings from Autorunne / autorunne to Autorunne / autorunne

### Task 2: Rebrand install/build metadata
- Update `pyproject.toml` package name, URLs, script entrypoints, description, and keywords
- Update CI/release references and wheel/install instructions
- Ensure package build artifacts will be named for Autorunne

### Task 3: Rebrand repo docs and usage docs
- Rewrite root README as Autorunne-first
- Rename usage docs to Autorunne filenames
- Remove stale `autorunne` / `.autorunne` references from tracked docs

### Task 4: Add business-facing docs
- Add a Chinese product overview/manual
- Add a Chinese commercial/business plan document
- Add a concise product positioning / monetization document

### Task 5: Verify
- Run targeted pytest suite
- Run CLI smoke checks through `python -m autorunne.cli`
- Build package to verify artifact naming
