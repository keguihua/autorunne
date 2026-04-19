# AI Workflow CLI

Make any repository **AI-ready in local development** without polluting the formal release version.

`awf` adds a private `.ai-workflow/` layer to a repo so Claude Code, Codex, Hermes, Cursor, and similar coding agents can resume work fast, follow the same workflow, and keep clean project memory.

## Why this exists
Most coding agents fail the same way:
- they lose context between sessions
- they over-edit unrelated files
- they do not know what was decided before
- they make cloned/open-source repos messy when you add internal workflow files

AI Workflow CLI solves that by separating two worlds:

### Development world
Local-only AI workflow files live under `.ai-workflow/` and help the agent understand:
- project context
- tasks
- decisions
- session history
- next action
- per-agent adapter rules

### Formal release world
Your release/export output stays clean and professional:
- no `.ai-workflow/`
- no internal AI notes
- no local-only workflow state

---

## What `awf` does
- initializes a reusable AI workflow for brand-new repos
- adopts existing or cloned repositories safely
- writes `.git/info/exclude` so local workflow files stay out of Git by default
- generates agent-readable project memory files
- supports VS Code auto-sync on folder open
- exports a clean release tree without internal workflow files
- supports multiple coding agents through shared docs + adapter files

---

## Who this is for
- solo builders using Claude Code / Codex / Hermes / Cursor
- teams who want a repeatable AI coding workflow
- people cloning open-source repos locally and wanting instant AI context
- people who want **development workflow and public release strictly separated**

---

## Current version
**0.2.0**

New in 0.2.0:
- stronger project detection for Next.js + pnpm
- stronger project detection for Go projects
- VS Code integration that can auto-run `awf sync` on folder open
- productized README and packaging metadata

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

### Option B — install with pipx from a git repo
When the repository is public, other users can install it directly:

```bash
pipx install git+https://github.com/keguihua/ai-workflow-cli.git
```

### Option C — install from a built package
You can also install from wheel / source package assets:

```bash
pip install ai_workflow_cli-0.2.0-py3-none-any.whl
```

---

## Build an installable package
Yes — if you want other users to use it cleanly, you should ship installable package artifacts.
This project now supports that.

Build locally:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
python -m build
```

That creates:
- `dist/*.whl`
- `dist/*.tar.gz`

These can be uploaded to a GitHub release or later published to PyPI.

---

## Quick start

### 1. New repo
```bash
git init
awf init
```

### 2. Existing repo or cloned GitHub repo
```bash
awf adopt
```

### 3. Existing repo + VS Code auto integration
```bash
awf adopt --with-vscode
```

### 4. Refresh workflow after work
```bash
awf sync --note "Finished auth fix, next handle dashboard filters"
```

### 5. Check status
```bash
awf status
```

### 6. Export a clean formal version
```bash
awf export
```

---

## Generated structure

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

---

## Commands

### `awf init`
Create the workflow in a git repo.

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
Refresh inferred state and append a manual note if needed.

```bash
awf sync
awf sync --note "Finished payments bugfix"
```

### `awf status`
Show workflow health and next action.

### `awf doctor`
Validate workflow structure and git isolation.

### `awf export`
Create a clean release copy without `.ai-workflow/`.

### `awf hooks`
Install git hooks that auto-run sync after checkout/merge.

### `awf vscode`
Create VS Code integration files manually.

```bash
awf vscode
```

---

## VS Code auto integration
This release adds a practical VS Code integration path.

If you run:

```bash
awf adopt --with-vscode
```

or

```bash
awf init --with-vscode
```

it creates:
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

The generated task uses `runOn: folderOpen`, so VS Code can automatically trigger `awf sync` when the workspace opens.

Note: VS Code may ask the user to allow automatic tasks the first time. The generated settings turn that on for the workspace.

---

## Stronger project detection
Current detection covers:
- generic git repos
- Node projects
- npm / pnpm / yarn / bun detection
- React / Next.js / Vite / Vue / Nuxt / Svelte / Express / NestJS signals
- Python projects
- FastAPI / Django / Flask / Streamlit signals
- pip / poetry / uv signals
- Go projects
- Rust projects

The tool infers:
- stack
- likely framework
- package manager
- likely run/test/build commands
- important files
- common source directories

---

## How other users should use it
For someone using this tool on their own machine:

### New project flow
1. create or clone a repo
2. run `awf init`
3. point their coding agent to `.ai-workflow/`
4. let the agent start from `NEXT_ACTION.md`
5. run `awf sync` after meaningful work
6. run `awf export` before packaging/release

### Cloned open-source repo flow
1. clone the repo normally
2. run `awf adopt`
3. optionally run `awf adopt --with-vscode`
4. keep `.ai-workflow/` local-only via `.git/info/exclude`
5. export a clean version if they want to package or fork-release it formally

---

## Git safety model
By default, `awf` writes `.ai-workflow/` into:

```text
.git/info/exclude
```

That means:
- safe for local-only workflow state
- safe for cloned open-source repos
- safer than forcing shared `.gitignore` changes

You can still choose your own repo policy later, but the default behavior avoids accidental pollution.

---

## Validation status
Validated locally for:
- generic repo initialization
- Node / React / Vite adoption
- Next.js + pnpm detection
- Python / FastAPI adoption
- Go detection
- `sync`, `doctor`, `export`, `hooks`, and `vscode` flows

Automated coverage:
- `pytest`
- GitHub Actions on Python 3.11 and 3.12

---

## Development

```bash
source .venv/bin/activate
pytest
python -m build
```

---

## Roadmap
- `awf release` command
- stronger project inference for more stacks
- file watcher mode for auto-sync
- richer release packaging
- PyPI publishing
- deeper editor integrations beyond VS Code

---

## License
MIT
