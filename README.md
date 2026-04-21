# Autorunne

[![CI](https://github.com/keguihua/autorunne/actions/workflows/ci.yml/badge.svg)](https://github.com/keguihua/autorunne/actions/workflows/ci.yml)
[![Release Packages](https://github.com/keguihua/autorunne/actions/workflows/release.yml/badge.svg)](https://github.com/keguihua/autorunne/actions/workflows/release.yml)

**Turn any Git repository into a durable AI coding workspace for Claude Code, Codex, Gemini, Hermes, Cursor, and GitHub Copilot.**

Autorunne is a **local-first workflow CLI** for people already building with coding agents but who are tired of losing project state between sessions.

It gives every repo a shared workflow core:
- project context
- tasks
- decisions
- session history
- next action
- agent-ready entry docs

At the same time, it keeps `.autorunne/` out of the formal release version.

## Why it is different
Most AI coding tools help write code once.

Autorunne is built for the harder problem:
- resuming work tomorrow without re-explaining the repo
- handing the same repo across Claude Code, Codex, Gemini, Hermes, Cursor, or GitHub Copilot
- keeping project memory local instead of trapped in one chat window
- finishing work cleanly with start → checkpoint → finish
- separating internal AI workflow state from the shipped product

## Best fit
- solo builders shipping client work
- developers using multiple coding-agent tools
- teams that want a simple repo-local memory layer, not a heavy AI platform

## Not trying to be
- a replacement IDE
- a giant autonomous-agent platform
- a chat wrapper with no durable project state

## Documentation
- [中文使用说明](docs/Autorunne-Usage-ZH.md)
- [English usage guide](docs/Autorunne-Usage-EN.md)
- [Autorunne 与大模型开发对接说明](docs/Autorunne-LLM-Integration-ZH.md)
- [Autorunne 自动识别 / 自动初始化 / 自动恢复](docs/Autorunne-Auto-Mode-ZH.md)
- [Autorunne 发布与合并策略](docs/Autorunne-Release-Playbook-ZH.md)
- [Autorunne 产品说明书](docs/Autorunne-产品说明书-ZH.md)
- [Autorunne 商业计划书](docs/Autorunne-商业计划书-ZH.md)
- [Autorunne 对外定位与销售话术](docs/Autorunne-对外定位与销售话术-ZH.md)

---

## What problem it solves
Most AI coding tools can edit code, but they are weak at:
- resuming cleanly tomorrow
- carrying project memory across sessions
- working safely inside cloned open-source repos
- separating private workflow state from public release output
- staying useful across editors instead of being locked into one IDE

Autorunne solves this by acting as a **workflow layer**, not just another chat wrapper.

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
   - the workflow lives in `.autorunne/`
   - agents plug into that shared context instead of inventing their own memory format

4. **Editors are entry points, not the core**
   - VS Code can auto-open and auto-bootstrap on folder open
   - the CLI remains the source of truth
   - this makes future support for other editors easier

---

## Current version
**0.5.0**

### New in 0.5.0
- adds `autorunne open` to auto-bootstrap missing workflow memory or resume existing repos immediately
- upgrades VS Code folder-open automation to call `autorunne open` instead of a plain sync
- adds project phase detection, recent git signal detection, and resume hints for half-finished repos
- refreshes `START_HERE.md`, `PROJECT_CONTEXT.md`, and `COMMANDS.md` for low-prompt / near-zero-prompt handoff
- keeps release bundles clean with a `MANIFEST.json`

### Previously added in 0.3.0
- `autorunne release`
- `autorunne completion`
- `autorunne hooks --with-pre-commit`
- stronger `autorunne doctor`
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

### Fastest install for VS Code terminal users
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```

This installs Autorunne with `pipx`, so you can open any repo in VS Code and immediately run:

```bash
autorunne open --with-vscode
```

Then just open the repo. Autorunne will auto-bootstrap or resume on open, and `.autorunne/START_HERE.md` becomes the agent entry point for Claude Code, Codex, Gemini, Hermes, Cursor, or GitHub Copilot.

### Option A — local development install
```bash
git clone https://github.com/keguihua/autorunne.git
cd autorunne
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Option B — install from release asset
```bash
pip install autorunne-0.5.0-py3-none-any.whl
```

### Option C — install directly with pipx once published
```bash
pipx install autorunne
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
autorunne init
```

### Existing repo or cloned GitHub repo
```bash
autorunne open
```

### Existing repo + VS Code auto integration
```bash
autorunne open --with-vscode
```

Then point your coding agent at `.autorunne/START_HERE.md` or just continue from the repo after Autorunne opens it.

### Start a focused task
```bash
autorunne start --task "Implement billing webhook" --next "Write webhook contract tests"
```

### Save a checkpoint during development
```bash
autorunne checkpoint --summary "Mapped webhook payloads" --next "Implement handler wiring"
```

### Refresh after meaningful work
```bash
autorunne sync --note "Finished auth fix, next handle dashboard filters"
```

### Close one slice cleanly
```bash
autorunne finish --summary "Implemented auth fix" --next "Review dashboard filters"
```

### Watch local changes and auto-sync
```bash
autorunne watch --duration 60 --interval 1
```

### Health check
```bash
autorunne doctor
```

### Export formal version
```bash
autorunne export
```

### Build release bundle
```bash
autorunne release --version 0.5.0
```

---

## Core commands

### `autorunne init`
Create the workflow layer.

```bash
autorunne init
autorunne init --with-vscode
```

### `autorunne adopt`
Scan an existing repository and generate workflow docs manually.

```bash
autorunne adopt
autorunne adopt --with-vscode
```

### `autorunne open`
Auto-bootstrap a half-finished repo if `.autorunne/` is missing, or resume the existing workflow memory if it already exists.

```bash
autorunne open
autorunne open --with-vscode
```

### `autorunne sync`
Refresh workflow state, keep your manual memory docs intact, and append a manual note.

### `autorunne start`
Open a new task slice and put it into `TASKS.md`.

```bash
autorunne start --task "Implement billing webhook" --next "Write webhook contract tests"
```

### `autorunne checkpoint`
Save progress mid-task without closing the task.

```bash
autorunne checkpoint --summary "Mapped webhook payloads" --next "Implement handler wiring"
```

### `autorunne finish`
Close a real task, append a completion summary, optionally capture a durable decision, and run validation before setting the next action.

```bash
autorunne finish --summary "Implemented auth fix" --task "Review dashboard filters" --next "Ship release notes" --decision "Dashboard filters now reuse shared auth state"
```

To force a specific validation command:

```bash
autorunne finish --summary "Kept tests green" --validate "pytest -q" --next "Ship changelog"
```

### `autorunne watch`
Watch the repository for file changes and auto-run sync.

```bash
autorunne watch --duration 120 --interval 1
```

### `autorunne doctor`
Validate:
- workflow files
- `.git/info/exclude`
- git hooks
- VS Code integration
- pre-commit setup
- package artifacts

### `autorunne export`
Create a clean formal export without `.autorunne/`.

### `autorunne release`
Create a release bundle under `.dist-release/releases/vX.Y.Z/` with:
- clean repo export
- release notes
- `MANIFEST.json`
- optional package assets

### `autorunne hooks`
Install git hooks.

```bash
autorunne hooks
autorunne hooks --with-pre-commit
```

### `autorunne vscode`
Create VS Code integration manually.

### `autorunne completion`
Print shell completion setup instructions.

```bash
autorunne completion bash
autorunne completion zsh
autorunne completion fish
```

---

## Generated workflow structure

```text
.autorunne/
├── PROJECT_CONTEXT.md
├── TASKS.md
├── DECISIONS.md
├── SESSION_LOG.md
├── RULES.md
├── NEXT_ACTION.md
├── COMMANDS.md
├── START_HERE.md
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
autorunne open --with-vscode
```

or

```bash
autorunne init --with-vscode
```

`autorunne` creates:
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

The generated task uses `runOn: folderOpen`, so VS Code can auto-trigger `autorunne open` when the workspace opens.

---

## Team-friendly usage
```bash
autorunne hooks --with-pre-commit
```

This gives you:
- post-checkout sync
- post-merge sync
- pre-commit validation via `autorunne doctor`
- local `.pre-commit-config.yaml` bootstrap

---

## Clean release separation
By default, `autorunne` writes `.autorunne/` into:

```text
.git/info/exclude
```

This keeps local workflow state out of normal repo history.

So you get:
- rich local Autorunne during development
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
2. run `autorunne init`
3. point the coding agent at `.autorunne/`
4. work from `NEXT_ACTION.md`
5. run `autorunne sync` or `autorunne watch`
6. run `autorunne export` or `autorunne release`

### Existing repo / cloned open-source repo
1. clone the repo normally
2. run `autorunne adopt`
3. optionally run `autorunne open --with-vscode`
4. keep `.autorunne/` local-only
5. export or release a clean formal version when needed

---

## Roadmap after 0.5.0
- publish to PyPI
- public `pipx` install flow
- smarter file watcher / daemon mode
- deeper monorepo graph awareness
- more editor entrypoints beyond VS Code
- stronger release automation (`autorunne release` + tag + changelog)

---

## License
MIT
