from __future__ import annotations

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
