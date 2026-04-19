# AI Workflow CLI

[![CI](https://github.com/keguihua/ai-workflow-cli/actions/workflows/ci.yml/badge.svg)](https://github.com/keguihua/ai-workflow-cli/actions/workflows/ci.yml)
[![Release Packages](https://github.com/keguihua/ai-workflow-cli/actions/workflows/release.yml/badge.svg)](https://github.com/keguihua/ai-workflow-cli/actions/workflows/release.yml)

**Make any repository AI-ready for local development, while keeping release output clean.**

`awf` is a local-first workflow CLI for Claude Code, Codex, Hermes, Cursor, and similar coding agents. It gives every repo a shared workflow core:
- project context
- tasks
- decisions
- session history
- next action
- per-agent adapter instructions

At the same time, it keeps `.ai-workflow/` out of the formal release version.

---

## What problem it solves
Most AI coding tools can edit code, but they are weak at:
- resuming cleanly tomorrow
- carrying project memory across sessions
- working safely inside cloned open-source repos
- separating private workflow state from public release output
- staying useful across editors instead of being locked into one IDE

AI Workflow CLI solves this by acting as a **workflow layer**, not just another chat wrapper.

---

## Product principles
This project is built around four product directions:

1. **Installation system**
   - behaves like a real developer CLI
   - ships release assets
   - is ready for `pipx` / PyPI style distribution

2. **Stronger project detection**
   - understands common stacks, workspace layouts, and build systems
   - gives agents immediate context in existing repos

3. **Unified workflow core layer**
   - the workflow lives in `.ai-workflow/`
   - agents plug into that shared context instead of inventing their own memory format

4. **Editors are entry points, not the core**
   - VS Code can auto-sync on folder open
   - the CLI remains the source of truth
   - this makes future support for other editors easier

---

## Current version
**0.4.0**

### New in 0.4.0
- adds `awf watch` for polling-based local auto-sync during development
- adds C and C++ detection (including CMake-based projects)
- strengthens Rust, Python, Node, monorepo, pnpm workspace, and Turborepo support
- improves release bundles with a `MANIFEST.json`
- prepares the project for more polished external presentation

### Previously added in 0.3.0
- `awf release`
- `awf completion`
- `awf hooks --with-pre-commit`
- stronger `awf doctor`
- monorepo / workspace / Turborepo detection

---

## Supported project types today
### Web / app / service stacks
- npm / pnpm / yarn / bun
- React
- Next.js
- Vite
- Vue
- Nuxt
- Svelte / SvelteKit
- Express
- NestJS
- monorepos / pnpm workspaces / Turborepo / Nx signals

### Python
- pip
- poetry
- uv
- FastAPI
- Django
- Flask
- Streamlit

### Systems / compiled languages
- Go
- Rust
- C
- C++
- CMake-based C/C++ projects

---

## Install

### Option A — local development install
```bash
git clone https://github.com/keguihua/ai-workflow-cli.git
cd ai-workflow-cli
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Option B — install from release asset
```bash
pip install ai_workflow_cli-0.4.0-py3-none-any.whl
```

### Planned public install path
```bash
pipx install ai-workflow-cli
```

---

## Build installable packages
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m build
```

Build artifacts:
- `dist/*.whl`
- `dist/*.tar.gz`

---

## Quick start

### New repo
```bash
git init
awf init
```

### Existing repo or cloned GitHub repo
```bash
awf adopt
```

### Existing repo + VS Code auto integration
```bash
awf adopt --with-vscode
```

### Refresh after meaningful work
```bash
awf sync --note "Finished auth fix, next handle dashboard filters"
```

### Watch local changes and auto-sync
```bash
awf watch --duration 60 --interval 1
```

### Health check
```bash
awf doctor
```

### Export formal version
```bash
awf export
```

### Build release bundle
```bash
awf release --version 0.4.0
```

---

## Core commands

### `awf init`
Create the workflow layer.

```bash
awf init
awf init --with-vscode
```

### `awf adopt`
Scan an existing repository and generate workflow docs.

```bash
awf adopt
awf adopt --with-vscode
```

### `awf sync`
Refresh workflow state and append a manual note.

### `awf watch`
Watch the repository for file changes and auto-run sync.

```bash
awf watch --duration 120 --interval 1
```

### `awf doctor`
Validate:
- workflow files
- `.git/info/exclude`
- git hooks
- VS Code integration
- pre-commit setup
- package artifacts

### `awf export`
Create a clean formal export without `.ai-workflow/`.

### `awf release`
Create a release bundle under `.dist-release/releases/vX.Y.Z/` with:
- clean repo export
- release notes
- `MANIFEST.json`
- optional package assets

### `awf hooks`
Install git hooks.

```bash
awf hooks
awf hooks --with-pre-commit
```

### `awf vscode`
Create VS Code integration manually.

### `awf completion`
Print shell completion setup instructions.

```bash
awf completion bash
awf completion zsh
awf completion fish
```

---

## Generated workflow structure

```text
.ai-workflow/
├── PROJECT_CONTEXT.md
├── TASKS.md
├── DECISIONS.md
├── SESSION_LOG.md
├── RULES.md
├── NEXT_ACTION.md
├── agents/
│   ├── common.md
│   ├── claude-code.md
│   ├── codex.md
│   ├── hermes.md
│   └── cursor.md
└── snapshots/
    └── latest.json
```

This is the shared workflow core. Editors and coding tools can come and go, but the project workflow stays stable.

---

## VS Code integration
VS Code is treated as an entry point, not the system core.

If you run:

```bash
awf adopt --with-vscode
```

or

```bash
awf init --with-vscode
```

`awf` creates:
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

The generated task uses `runOn: folderOpen`, so VS Code can auto-trigger `awf sync` when the workspace opens.

---

## Team-friendly usage
```bash
awf hooks --with-pre-commit
```

This gives you:
- post-checkout sync
- post-merge sync
- pre-commit validation via `awf doctor`
- local `.pre-commit-config.yaml` bootstrap

---

## Clean release separation
By default, `awf` writes `.ai-workflow/` into:

```text
.git/info/exclude
```

This keeps local workflow state out of normal repo history.

So you get:
- rich local AI workflow during development
- safe adoption for cloned open-source repos
- clean formal release output

---

## Validation status
Validated locally for:
- generic repo initialization
- Node / React / Vite / Next.js / pnpm workspace / Turborepo detection
- Python / FastAPI detection
- Go detection
- Rust detection
- C and C++ / CMake detection
- VS Code auto integration
- release bundle generation
- shell completion output
- pre-commit and hook installation
- watcher-based auto-sync flow

Automated validation:
- `pytest`
- GitHub Actions on Python 3.11 and 3.12
- release workflow uploads wheel + source tarball

---

## Install/use path for other developers
### New project
1. create a repo
2. run `awf init`
3. point the coding agent at `.ai-workflow/`
4. work from `NEXT_ACTION.md`
5. run `awf sync` or `awf watch`
6. run `awf export` or `awf release`

### Existing repo / cloned open-source repo
1. clone the repo normally
2. run `awf adopt`
3. optionally run `awf adopt --with-vscode`
4. keep `.ai-workflow/` local-only
5. export or release a clean formal version when needed

---

## Roadmap after 0.4.0
- publish to PyPI
- public `pipx` install flow
- smarter file watcher / daemon mode
- deeper monorepo graph awareness
- more editor entrypoints beyond VS Code
- stronger release automation (`awf release` + tag + changelog)

---

## License
MIT
