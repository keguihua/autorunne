# AI Workflow CLI

A local-first CLI that attaches a reusable AI development workflow to any repository while keeping public releases clean.

## What it does
- Initializes a private `.ai-workflow/` layer for new repos
- Adopts existing or cloned repos without polluting upstream history
- Generates reusable project memory docs for any coding agent
- Keeps `.ai-workflow/` out of Git by default via `.git/info/exclude`
- Exports a clean release copy without AI workflow files

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .[dev]

awf init
awf adopt
awf status
awf sync --note "Finished auth fix, next check dashboard filters"
awf export
```

## Commands
- `awf init` — create workflow files for a repo
- `awf adopt` — scan an existing repo and generate workflow docs
- `awf sync` — refresh inferred state and next action
- `awf status` — show current workflow health and next step
- `awf doctor` — validate git exclusion and workflow structure
- `awf export` — create a clean copy without `.ai-workflow/`

## Development

```bash
source .venv/bin/activate
pytest
```
