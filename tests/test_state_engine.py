from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from autorunne.cli import app

runner = CliRunner()


def _run_in(repo: Path, args: list[str]):
    old = Path.cwd()
    try:
        import os

        os.chdir(repo)
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old)


def test_render_rebuilds_deleted_view_from_state(python_repo: Path):
    init_result = _run_in(python_repo, ["init"])
    assert init_result.exit_code == 0

    start_here = python_repo / ".autorunne" / "views" / "START_HERE.md"
    assert start_here.exists()
    start_here.unlink()
    assert not start_here.exists()

    render_result = _run_in(python_repo, ["render"])
    assert render_result.exit_code == 0
    assert start_here.exists()
    assert "Zero-prompt handoff" in start_here.read_text(encoding="utf-8")


def test_open_imports_legacy_markdown_workspace(python_repo: Path):
    workflow_root = python_repo / ".autorunne"
    workflow_root.mkdir()
    (workflow_root / "NEXT_ACTION.md").write_text("# Next Action\n\nLegacy next step\n", encoding="utf-8")
    (workflow_root / "TASKS.md").write_text(
        "# Tasks\n\n## Completed / inferred\n\n## In progress\n- [ ] Legacy in-progress task\n\n## Next up\n- [ ] Legacy next step\n\n## Known unknowns\n- [ ] Legacy unknown\n",
        encoding="utf-8",
    )

    result = _run_in(python_repo, ["open"])
    assert result.exit_code == 0
    current_text = (workflow_root / "state" / "current.json").read_text(encoding="utf-8")
    tasks_text = (workflow_root / "views" / "TASKS.md").read_text(encoding="utf-8")
    assert "Legacy next step" in current_text
    assert "Legacy in-progress task" in tasks_text


def test_sync_preserves_explicit_next_action_from_state(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    _run_in(python_repo, ["start", "--task", "Keep auth stable", "--next", "Custom next step"])

    result = _run_in(python_repo, ["sync"])
    assert result.exit_code == 0

    current_text = (python_repo / ".autorunne" / "state" / "current.json").read_text(encoding="utf-8")
    next_text = (python_repo / ".autorunne" / "views" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    assert "Custom next step" in current_text
    assert "Custom next step" in next_text


def test_sync_renders_haopay_style_monorepo_from_packages(haopay_style_monorepo: Path):
    result = _run_in(haopay_style_monorepo, ["sync"])
    assert result.exit_code == 0

    state_root = haopay_style_monorepo / ".autorunne" / "state"
    views_root = haopay_style_monorepo / ".autorunne" / "views"
    current = json.loads((state_root / "current.json").read_text(encoding="utf-8"))
    start_here = (views_root / "START_HERE.md").read_text(encoding="utf-8")
    project_context = (views_root / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
    commands = (views_root / "COMMANDS.md").read_text(encoding="utf-8")

    assert current["stack"] == ["multi-package Node/TypeScript"]
    assert "generic" not in current["stack"]
    assert "Vite frontend" in current["framework"]
    assert "Node.js backend" in current["framework"]
    assert "Hardhat smart contracts" in current["framework"]
    assert current["commands"]["frontend:build"] == "cd frontend && npm run build"
    assert current["commands"]["backend:test"] == "cd backend && npm test"
    assert current["commands"]["contracts:compile"] == "cd contracts && npm run compile"
    assert current["commands"]["contracts:test"] == "cd contracts && npm test"

    assert "Stack: generic" not in start_here
    assert "Stack: multi-package Node/TypeScript" in start_here
    assert "Vite frontend" in project_context
    assert "Package manager: npm per package" in project_context
    assert "frontend/package.json" in project_context
    assert "backend/package.json" in project_context
    assert "contracts/package.json" in project_context
    assert "No reliable run/test/build commands detected yet" not in commands
    assert "cd frontend && npm run build" in commands
    assert "cd backend && npm test" in commands
    assert "cd contracts && npm run compile" in commands


def test_render_uses_packages_when_existing_current_summary_is_generic(haopay_style_monorepo: Path):
    _run_in(haopay_style_monorepo, ["sync"])
    state_file = haopay_style_monorepo / ".autorunne" / "state" / "current.json"
    current = json.loads(state_file.read_text(encoding="utf-8"))
    packages = current["packages"]
    current["stack"] = ["generic"]
    current["framework"] = ["generic"]
    current["package_manager"] = ["unknown"]
    current["commands"] = {}
    current["packages"] = packages
    state_file.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = _run_in(haopay_style_monorepo, ["render"])
    assert result.exit_code == 0

    commands = (haopay_style_monorepo / ".autorunne" / "views" / "COMMANDS.md").read_text(encoding="utf-8")
    start_here = (haopay_style_monorepo / ".autorunne" / "views" / "START_HERE.md").read_text(encoding="utf-8")
    assert "Stack: generic" not in start_here
    assert "Stack: multi-package Node/TypeScript" in start_here
    assert "No reliable run/test/build commands detected yet" not in commands
    assert "cd frontend && npm run build" in commands


def test_checkpoint_records_validation_details(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    result = _run_in(
        python_repo,
        ["checkpoint", "--summary", "Saved progress", "--next", "Continue slice", "--validate", "pytest -q"],
    )
    assert result.exit_code == 0
    assert "Validation: passed" in result.stdout

    sessions_text = (python_repo / ".autorunne" / "state" / "sessions.json").read_text(encoding="utf-8")
    assert "Validation command" in sessions_text
    assert "pytest -q" in sessions_text


def test_finish_records_structured_state_details(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    (python_repo / "src" / "app.py").write_text("print('state changed')\n", encoding="utf-8")

    result = _run_in(
        python_repo,
        ["finish", "--summary", "Recorded state detail", "--validate", "pytest -q", "--next", "Ship docs"],
    )
    assert result.exit_code == 0

    state_root = python_repo / ".autorunne" / "state"
    sessions_text = (state_root / "sessions.json").read_text(encoding="utf-8")
    events_text = (state_root / "events.jsonl").read_text(encoding="utf-8")
    current_text = (state_root / "current.json").read_text(encoding="utf-8")

    assert "Recorded state detail" in sessions_text
    assert "git_status" in sessions_text
    assert "diff_stat" in sessions_text
    assert "validation" in sessions_text
    assert "task_finished" in events_text
    assert "Ship docs" in current_text
