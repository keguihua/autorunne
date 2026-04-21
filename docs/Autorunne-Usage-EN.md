# Autorunne Usage Guide (English)

## 1. What this tool is for
Autorunne (`autorunne`) adds a private local Autorunne layer to any Git repository while keeping formal release artifacts clean.

It is designed for:
- brand-new projects
- in-progress projects
- cloned open-source repositories
- teams or solo builders who want Claude Code, Codex, Hermes, Cursor, and similar agents to resume work quickly

## 2. Core upgrades in 0.6.0
- improves `scripts/install.sh` for cleaner public installation
- supports pinned public release-wheel installs
- adds `--max-syncs` to `autorunne daemon`
- shows the last changed files in daemon output
- adds a GitHub-visible Chinese operator manual for installation and daily use
- clarifies the real day-to-day workflow: install Autorunne once, initialize each repo once, then launch Codex or Claude Code directly from the repo terminal

## 3. Supported languages / project types
### Web / app / service
- npm / pnpm / yarn / bun
- React
- Next.js
- Vite
- Vue
- Nuxt
- Svelte / SvelteKit
- Express
- NestJS
- monorepo / pnpm workspace / Turborepo / Nx signals

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
- CMake-style C/C++ projects

## 4. Installation
### Fastest install (ideal for a single command in a VS Code terminal)
```bash
curl -fsSL https://raw.githubusercontent.com/keguihua/autorunne/main/scripts/install.sh | bash
```

After install, enter your repo and run:
```bash
autorunne open --with-vscode
```

After that, just open the repo normally. Autorunne will auto-bootstrap or resume on open, and `.autorunne/START_HERE.md` remains the clean agent entry point.

### Development install
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

### Install from release artifact
```bash
pip install autorunne-0.6.0-py3-none-any.whl
```

### Recommended public install path later
```bash
pipx install autorunne
```

## 5. Main commands
### Initialize a new repository
```bash
autorunne init
autorunne init --with-vscode
```

### Adopt or resume an existing repository
```bash
autorunne open
autorunne open --with-vscode
```

On the first open of an older repo, Autorunne will create `.autorunne/`. On later opens, it will refresh and resume the existing workflow state.

### Keep a repo warm locally
```bash
autorunne daemon --duration 300 --interval 2
```

### Push a Hermes chat request into local workflow memory
```bash
autorunne hermes-task \
  --task "Continue billing integration" \
  --next "Write Stripe webhook contract test" \
  --context "User asked Hermes to keep moving without re-explaining the repo"
```

### Start a focused task
```bash
autorunne start --task "Implement billing webhook" --next "Write webhook contract tests"
```

### Save a checkpoint mid-task
```bash
autorunne checkpoint --summary "Mapped webhook payloads" --next "Implement handler wiring"
```

### Refresh workflow state
```bash
autorunne sync
autorunne sync --note "Finished auth fix, next check the order page"
```

### Close one development slice
```bash
autorunne finish --summary "Implemented auth fix" --task "Review dashboard filters" --next "Ship release notes" --decision "Dashboard filters now reuse shared auth state"
```

### Force a specific validation command
```bash
autorunne finish --summary "Kept tests green" --validate "pytest -q" --next "Ship changelog"
```

### Watch local file changes
```bash
autorunne watch --duration 60 --interval 1
```

### Validate workflow health
```bash
autorunne doctor
```

### Export a clean formal release
```bash
autorunne export
```

### Create a release bundle
```bash
autorunne release --version 0.6.0
```

### Install hooks and pre-commit support
```bash
autorunne hooks --with-pre-commit
```

### Print shell completion setup
```bash
autorunne completion zsh
```

## 6. Generated structure
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
│   ├── cursor.md
│   └── copilot.md
└── snapshots/
    └── latest.json
```

## 7. VS Code auto integration
Run:
```bash
autorunne open --with-vscode
```

This generates:
- `.vscode/tasks.json`
- `.vscode/settings.json`
- `.vscode/extensions.json`

and allows VS Code to auto-run `autorunne open` on folder open.

## 8. Clean release separation
The tool isolates `.autorunne/` with `.git/info/exclude` by default.
That means:
- local development keeps a rich Autorunne layer
- upstream/public repositories stay clean by default
- `autorunne export` and `autorunne release` outputs do not include `.autorunne/`

## 9. Validation status
This version has been validated for:
- generic empty repo initialization
- Node / React / Vite / Next.js / pnpm workspace / Turborepo detection
- Python / FastAPI detection
- Go / Rust detection
- C / C++ / CMake detection
- `sync`, `watch`, `doctor`, `export`, `release`, `hooks`, and `completion`
- local pytest coverage
- wheel installation validation
- GitHub Actions on Python 3.11 and 3.12

## 10. Model compatibility
The workflow is model-agnostic and intended for:
- Claude Code
- Codex
- Gemini
- Hermes
- Cursor Agent
- GitHub Copilot / Copilot Chat
- other coding agents that can read project files

## 11. Suggested next steps
Good future upgrades:
- publish to PyPI
- public `pipx` install flow
- smarter watcher / background daemon mode
- deeper monorepo awareness
- more editor entrypoints beyond VS Code
