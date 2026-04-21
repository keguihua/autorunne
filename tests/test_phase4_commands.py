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
