# AI Workflow CLI

Turn **any repository** into an **AI-ready local development workspace** while keeping the formal release version clean.

`awf` gives Claude Code, Codex, Hermes, Cursor, and similar coding agents a shared repo-local workflow layer:
- project context
- current tasks
- decisions
- session history
- next action
- per-agent adapter instructions

At the same time, it keeps `.ai-workflow/` out of the formal release output.

---

## Why this is different
Most AI coding tools are good at editing code, but weak at:
- resuming a project cleanly tomorrow
- working safely inside cloned open-source repos
- separating private workflow state from public release output
- staying useful across editors instead of being locked into one IDE

AI Workflow CLI is built around four product directions:
1. **Installation system** — installable like a real developer tool
2. **Stronger project detection** — not just one stack or one framework
3. **Unified workflow core layer** — one repo-local workflow shared by all coding agents
4. **Editors as entry points, not the core** — VS Code can plug in, but the CLI stays the source of truth

---

## Current version
**0.3.0**

### New in 0.3.0
- `awf release` creates a formal release bundle with clean export + release notes
- stronger detection for monorepos / pnpm workspaces / Turborepo
- stronger detection for Next.js + pnpm, Go, Rust, Python, and common Node stacks
- enhanced `awf doctor` with checks for workflow files, git exclude, hooks, VS Code, pre-commit, and package artifacts
- `awf completion` for shell setup instructions
- `awf hooks --with-pre-commit` for team-friendly repo validation
- improved packaging story for real installation and release assets

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

### Option B — preferred user install once public / published
```bash
pipx install ai-workflow-cli
```

### Option C — install from GitHub release asset
```bash
pip install ai_workflow_cli-0.3.0-py3-none-any.whl
```

---

## Build installable packages
This project now behaves like a real Python CLI product.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m build
```

Build artifacts:
- `dist/*.whl`
- `dist/*.tar.gz`

These can be attached to GitHub Releases and installed directly by users.

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

### Refresh workflow after meaningful work
```bash
awf sync --note "Finished auth fix, next handle dashboard filters"
```

### Check health
```bash
awf doctor
```

### Export formal version
```bash
awf export
```

### Build a release bundle
```bash
awf release --version 0.3.0
```

---

## Core commands

### `awf init`
Create a workflow layer for a repo.

```bash
awf init
awf init --with-vscode
```

### `awf adopt`
Scan an existing repo and generate workflow docs.

```bash
awf adopt
awf adopt --with-vscode
```

### `awf sync`
Refresh inferred state and append a manual note.

```bash
awf sync
awf sync --note "Finished payments bugfix"
```

### `awf status`
Show workflow health and next action.

### `awf doctor`
Validate:
- workflow files
- `.git/info/exclude`
- git hooks
- VS Code integration
- pre-commit setup
- package artifacts

### `awf export`
Create a clean export without `.ai-workflow/`.

### `awf release`
Create a release bundle under `.dist-release/releases/vX.Y.Z/` with:
- clean repo export
- release notes
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

This is the shared core layer. Editors and coding tools can come and go, but the project workflow stays the same.

---

## Stronger project detection
Current detection covers:
- generic git repos
- npm / pnpm / yarn / bun
- React / Next.js / Vite / Vue / Nuxt / Svelte / Express / NestJS
- Python / pip / poetry / uv / FastAPI / Django / Flask / Streamlit
- Go projects
- Rust projects
- monorepos / pnpm workspaces / Turborepo / Nx signals

The tool infers:
- stack
- framework
- package manager
- likely run / test / build commands
- important files
- source directories

---

## VS Code integration
VS Code is treated as an **entry point**, not the system core.

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

## Team-friendly workflow
Use git hooks and pre-commit support to bring the workflow into team repos without making editors the center of everything.

```bash
awf hooks --with-pre-commit
```

That gives you:
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
- clean release/export output

---

## Validation status
Validated locally for:
- generic repo initialization
- Node / React / Vite adoption
- Next.js + pnpm detection
- monorepo workspace detection
- Python / FastAPI adoption
- Go detection
- VS Code auto integration
- release bundle generation
- shell completion output
- pre-commit and hook installation

Automated validation:
- `pytest`
- GitHub Actions on Python 3.11 and 3.12
- release workflow uploads wheel + source tarball

---

## Roadmap after 0.3.0
- PyPI publishing
- `pipx`-first public install flow
- shell completion install shortcuts
- file watcher mode for auto-sync
- deeper monorepo awareness
- more editor integrations beyond VS Code

---

## License
MIT
