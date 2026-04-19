# AI Workflow CLI Usage Guide (English)

## 1. What this tool is for
AI Workflow CLI (`awf`) adds a private local AI workflow layer to any Git repository while keeping formal release artifacts clean.

It is designed for:
- brand-new projects
- in-progress projects
- cloned open-source repositories
- teams or solo builders who want Claude Code, Codex, Hermes, Cursor, and similar agents to resume work quickly

## 2. Core upgrades in 0.3.0
- adds `awf release` for clean formal release bundles with release notes
- stronger detection for monorepos / pnpm workspaces / Turborepo / Next.js / Go / Rust
- stronger `awf doctor` checks for workflow files, git exclude, hooks, VS Code, pre-commit, and package artifacts
- adds `awf completion` for bash / zsh / fish
- adds `awf hooks --with-pre-commit` for team-friendly repository setup

## 3. Installation
### Development install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Recommended public install path later
```bash
pipx install ai-workflow-cli
```

### Install from release artifact
```bash
pip install ai_workflow_cli-0.3.0-py3-none-any.whl
```

## 4. Main commands
### Initialize a new repository
```bash
awf init
awf init --with-vscode
```

### Adopt an existing repository
```bash
awf adopt
awf adopt --with-vscode
```

### Refresh workflow state
```bash
awf sync
awf sync --note "Finished auth fix, next check the order page"
```

### Validate workflow health
```bash
awf doctor
```

### Export a clean formal release
```bash
awf export
```

### Create a release bundle
```bash
awf release --version 0.3.0
```

### Install hooks and pre-commit support
```bash
awf hooks --with-pre-commit
```

### Print shell completion setup
```bash
awf completion zsh
```

## 5. Generated structure
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

## 6. VS Code auto integration
Run:
```bash
awf adopt --with-vscode
```

This generates:
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

and allows VS Code to auto-run `awf sync` on folder open.

## 7. Clean release separation
The tool isolates `.ai-workflow/` with `.git/info/exclude` by default.
That means:
- local development keeps a rich AI workflow layer
- upstream/public repositories stay clean by default
- `awf export` and `awf release` outputs do not include `.ai-workflow/`

## 8. Validation status
This version has been validated for:
- generic empty repo initialization
- Node / React / Vite / Next.js / pnpm workspace / Turborepo detection
- Python / FastAPI detection
- Go detection
- `sync`, `doctor`, `export`, `release`, `hooks`, and `completion`
- local pytest coverage
- wheel installation validation
- GitHub Actions on Python 3.11 and 3.12

## 9. Model compatibility
The workflow is model-agnostic and intended for:
- Claude Code
- Codex
- Hermes
- Cursor Agent
- other coding agents that can read project files

## 10. Suggested next steps
Good future upgrades:
- publish to PyPI
- public `pipx` install flow
- file watcher based auto-sync
- deeper monorepo awareness
- more editor entrypoints beyond VS Code
