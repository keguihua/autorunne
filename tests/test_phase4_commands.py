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


def test_record_show_history_and_trace_commands(python_repo: Path):
    _run_in(python_repo, ["adopt"])

    record_result = _run_in(
        python_repo,
        [
            "record",
            "--summary",
            "Captured API review note",
            "--decision",
            "Keep the API surface state-first.",
            "--next",
            "Add state trace docs",
            "--task",
            "Document record command",
        ],
    )
    assert record_result.exit_code == 0
    assert "Recorded: Captured API review note" in record_result.stdout

    show_result = _run_in(python_repo, ["show", "--section", "current"])
    assert show_result.exit_code == 0
    assert "Add state trace docs" in show_result.stdout

    history_result = _run_in(python_repo, ["history", "--limit", "3"])
    assert history_result.exit_code == 0
    assert "Captured API review note" in history_result.stdout

    trace_result = _run_in(python_repo, ["trace", "--limit", "10"])
    assert trace_result.exit_code == 0
    assert "manual_recorded" in trace_result.stdout


def test_doctor_checks_renderability_and_integrations(python_repo: Path):
    _run_in(python_repo, ["open"])
    result = _run_in(python_repo, ["doctor"])
    assert result.exit_code == 1
    assert "render_rebuild" in result.stdout
    assert "integrations" in result.stdout
    assert "wrappers" in result.stdout


def test_show_events_section_exposes_manual_record(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    _run_in(python_repo, ["record", "--summary", "Track event stream"])
    result = _run_in(python_repo, ["show", "--section", "events"])
    assert result.exit_code == 0
    assert "manual_recorded" in result.stdout


def test_migrate_turns_legacy_workspace_into_state_workspace(python_repo: Path):
    workflow_root = python_repo / ".autorunne"
    workflow_root.mkdir()
    (workflow_root / "NEXT_ACTION.md").write_text("# Next Action\n\nLegacy next step\n", encoding="utf-8")
    (workflow_root / "TASKS.md").write_text(
        "# Tasks\n\n## Completed / inferred\n\n## In progress\n- [ ] Legacy in-progress task\n\n## Next up\n- [ ] Legacy next step\n",
        encoding="utf-8",
    )

    status_before = _run_in(python_repo, ["status"])
    assert status_before.exit_code == 0
    assert "Legacy workspace" in status_before.stdout

    migrate_result = _run_in(python_repo, ["migrate"])
    assert migrate_result.exit_code == 0
    assert "Migrated Autorunne workspace" in migrate_result.stdout

    show_result = _run_in(python_repo, ["show", "--section", "current"])
    assert show_result.exit_code == 0
    assert "Legacy next step" in show_result.stdout


def test_task_command_can_add_complete_and_remove_items(python_repo: Path):
    _run_in(python_repo, ["adopt"])

    add_result = _run_in(python_repo, ["task", "add", "--text", "Confirm rollout checklist", "--section", "next-up"])
    assert add_result.exit_code == 0
    assert "Confirm rollout checklist" in add_result.stdout

    unknown_result = _run_in(
        python_repo,
        ["task", "add", "--text", "Confirm external API quota", "--section", "known-unknowns"],
    )
    assert unknown_result.exit_code == 0

    done_result = _run_in(python_repo, ["task", "done", "--match", "Confirm rollout checklist"])
    assert done_result.exit_code == 0
    assert "Completed task" in done_result.stdout

    remove_result = _run_in(python_repo, ["task", "remove", "--match", "external API quota", "--section", "known-unknowns"])
    assert remove_result.exit_code == 0
    assert "Removed task" in remove_result.stdout

    tasks_text = (python_repo / ".autorunne" / "views" / "TASKS.md").read_text(encoding="utf-8")
    assert "[x] Confirm rollout checklist" in tasks_text
    assert "Confirm external API quota" not in tasks_text
