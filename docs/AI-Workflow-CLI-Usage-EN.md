# AI Workflow CLI Usage Guide (English)

## 1. What this tool is for
AI Workflow CLI (`awf`) adds a private local AI workflow layer to any Git repository while keeping public release artifacts clean.

It is designed for:
- brand-new projects
- in-progress projects
- cloned open-source repositories
- teams or solo builders who want Claude Code, Codex, Hermes, Cursor, and similar agents to resume work quickly

## 2. Core features
- Creates a dedicated `.ai-workflow/` directory
- Generates project context, tasks, decisions, session log, rules, and next action files
- Uses `.git/info/exclude` by default to avoid polluting upstream repositories
- Exports a clean formal release without the AI workflow layer
- Supports git hooks for post-checkout / post-merge workflow refreshes

## 3. Installation
```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]
```

Then run:
```bash
awf --help
```

## 4. Main commands
### Initialize a new repository
```bash
awf init
```

### Adopt an existing repository
```bash
awf adopt
```

### Refresh workflow state
```bash
awf sync
awf sync --note "Finished auth fix, next check the order page"
```

### Show current workflow status
```bash
awf status
```

### Validate workflow health
```bash
awf doctor
```

### Export a clean formal release
```bash
awf export
```

### Install auto-sync hooks
```bash
awf hooks
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

## 6. Recommended daily workflow
1. Run `awf adopt` or `awf init`
2. Make your coding agent read the shared workflow docs under `.ai-workflow/`
3. Start from `NEXT_ACTION.md`
4. After meaningful work, run `awf sync --note "what changed"`
5. Before publishing, run `awf export`

## 7. Clean release separation
The tool isolates `.ai-workflow/` with `.git/info/exclude` by default.
That means:
- local development can keep a rich AI workflow layer
- upstream/public repositories stay clean by default
- `awf export` produces a formal release tree without `.ai-workflow/`

## 8. Validation status
This version has been validated for:
- generic empty repo initialization
- Node / React / Vite style adoption
- Python / FastAPI style adoption
- working `sync`, `doctor`, `export`, and `hooks` commands
- local pytest coverage
- GitHub Actions CI on Python 3.11 and 3.12

## 9. Model compatibility
The workflow is model-agnostic and intended for:
- Claude Code
- Codex
- Hermes
- Cursor Agent
- other coding agents that can read project files

## 10. Suggested next steps
Good future upgrades:
- VS Code extension
- file watcher based auto-sync
- `awf release` publishing command
- deeper project structure detection
