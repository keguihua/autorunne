import json
import os
import threading
import time
from pathlib import Path

from typer.testing import CliRunner

from autorunne.cli import app

runner = CliRunner()


def _run_in(repo: Path, args: list[str]):
    old = Path.cwd()
    os.chdir(repo)
    try:
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old)


def test_init_creates_workflow_files(git_repo: Path):
    result = _run_in(git_repo, ["init"])
    assert result.exit_code == 0
    workflow_root = git_repo / ".autorunne"
    assert workflow_root.exists()
    assert (workflow_root / "PROJECT_CONTEXT.md").exists()
    assert (workflow_root / "agents" / "codex.md").exists()
    exclude_text = (git_repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert ".autorunne/" in exclude_text


def test_adopt_scans_existing_repo(node_repo: Path):
    result = _run_in(node_repo, ["adopt"])
    assert result.exit_code == 0
    content = (node_repo / ".autorunne" / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
    assert "Stack: node" in content
    assert "Framework: react, vite" in content


def test_init_can_install_vscode_workspace_integration(git_repo: Path):
    result = _run_in(git_repo, ["init", "--with-vscode"])
    assert result.exit_code == 0
    tasks_path = git_repo / ".vscode" / "tasks.json"
    settings_path = git_repo / ".vscode" / "settings.json"
    assert tasks_path.exists()
    assert settings_path.exists()
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    first_task = tasks["tasks"][0]
    assert first_task["label"] == "Autorunne: Sync on folder open"
    assert first_task["runOptions"]["runOn"] == "folderOpen"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["task.allowAutomaticTasks"] == "on"


def test_status_reports_missing_before_init(git_repo: Path):
    result = _run_in(git_repo, ["status"])
    assert result.exit_code == 0
    assert "PROJECT_CONTEXT.md" in result.stdout


def test_sync_appends_summary_and_updates_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    initial_log = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")

    result = _run_in(python_repo, ["sync", "--note", "checked auth flow"])
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")

    assert log_text != initial_log
    assert "checked auth flow" in log_text
    assert "sync" in log_text.lower()
    expected_next_action = " ".join(result.stdout.split("Next action:", 1)[1].split())
    actual_next_action = " ".join(next_action_text.split())
    assert expected_next_action in actual_next_action


def test_sync_without_note_appends_automatic_session_entry(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    initial_log = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")

    result = _run_in(python_repo, ["sync"])
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert log_text != initial_log
    assert "sync summary" in log_text.lower()
    assert "Next action:" in log_text


def test_finish_appends_summary_and_updates_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    result = _run_in(
        python_repo,
        ["finish", "--summary", "Implemented auth fix", "--next", "Review dashboard filters"],
    )
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")

    assert "finish summary" in log_text.lower()
    assert "Implemented auth fix" in log_text
    assert "Review dashboard filters" in log_text
    assert "Review dashboard filters" in next_action_text
    assert "Finished:" in result.stdout


def test_watch_detects_file_changes_and_syncs(node_repo: Path):
    _run_in(node_repo, ["adopt"])

    def mutate_file():
        time.sleep(0.2)
        (node_repo / "src" / "index.js").write_text("console.log('changed')\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_file)
    thread.start()
    result = _run_in(node_repo, ["watch", "--duration", "0.8", "--interval", "0.1"])
    thread.join()
    assert result.exit_code == 0
    assert "Detected change" in result.stdout


def test_doctor_warns_when_workflow_missing(git_repo: Path):
    result = _run_in(git_repo, ["doctor"])
    assert result.exit_code == 1
    assert "Autorunne workspace does not exist yet" in result.stdout


def test_doctor_checks_vscode_and_hooks(git_repo: Path):
    _run_in(git_repo, ["init", "--with-vscode"])
    result = _run_in(git_repo, ["doctor"])
    assert result.exit_code == 1
    assert "Git hooks are not installed" in result.stdout
    assert "Pre-commit config is not installed" in result.stdout
    _run_in(git_repo, ["hooks", "--with-pre-commit"])
    result_ok = _run_in(git_repo, ["doctor"])
    assert result_ok.exit_code == 0
    assert "ok" in result_ok.stdout.lower()


def test_export_creates_clean_copy_without_autorunne(node_repo: Path):
    _run_in(node_repo, ["adopt"])
    result = _run_in(node_repo, ["export"])
    assert result.exit_code == 0
    export_dir = node_repo / ".dist-release" / node_repo.name
    assert export_dir.exists()
    assert not (export_dir / ".autorunne").exists()
    assert (export_dir / "package.json").exists()


def test_release_creates_notes_and_manifest_and_clean_export(node_repo: Path):
    _run_in(node_repo, ["adopt"])
    result = _run_in(node_repo, ["release", "--version", "0.4.0", "--skip-build"])
    assert result.exit_code == 0
    release_dir = node_repo / ".dist-release" / "releases" / "v0.4.0"
    assert (release_dir / "repo").exists()
    assert (release_dir / "RELEASE_NOTES.md").exists()
    assert (release_dir / "MANIFEST.json").exists()
    assert not (release_dir / "repo" / ".autorunne").exists()


def test_completion_command_outputs_shell_snippet(git_repo: Path):
    result = _run_in(git_repo, ["completion", "zsh"])
    assert result.exit_code == 0
    assert "_AUTORUNNE_COMPLETE=zsh_source autorunne" in result.stdout


def test_hooks_install_writes_git_hooks_and_precommit(git_repo: Path):
    result = _run_in(git_repo, ["hooks", "--with-pre-commit"])
    assert result.exit_code == 0
    assert (git_repo / ".git" / "hooks" / "post-checkout").exists()
    assert (git_repo / ".git" / "hooks" / "post-merge").exists()
    assert (git_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (git_repo / ".pre-commit-config.yaml").exists()
