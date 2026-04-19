import json
import os
from pathlib import Path

from typer.testing import CliRunner

from awf.cli import app

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
    workflow_root = git_repo / ".ai-workflow"
    assert workflow_root.exists()
    assert (workflow_root / "PROJECT_CONTEXT.md").exists()
    assert (workflow_root / "agents" / "codex.md").exists()
    exclude_text = (git_repo / ".git" / "info" / "exclude").read_text(encoding="utf-8")
    assert ".ai-workflow/" in exclude_text


def test_adopt_scans_existing_repo(node_repo: Path):
    result = _run_in(node_repo, ["adopt"])
    assert result.exit_code == 0
    content = (node_repo / ".ai-workflow" / "PROJECT_CONTEXT.md").read_text(encoding="utf-8")
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
    assert first_task["label"] == "AWF: Sync on folder open"
    assert first_task["runOptions"]["runOn"] == "folderOpen"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    assert settings["task.allowAutomaticTasks"] == "on"


def test_status_reports_missing_before_init(git_repo: Path):
    result = _run_in(git_repo, ["status"])
    assert result.exit_code == 0
    assert "PROJECT_CONTEXT.md" in result.stdout


def test_sync_appends_note(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    result = _run_in(python_repo, ["sync", "--note", "checked auth flow"])
    assert result.exit_code == 0
    log_text = (python_repo / ".ai-workflow" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "checked auth flow" in log_text


def test_doctor_warns_when_workflow_missing(git_repo: Path):
    result = _run_in(git_repo, ["doctor"])
    assert result.exit_code == 1
    assert "Workflow directory does not exist yet" in result.stdout


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


def test_export_creates_clean_copy_without_ai_workflow(node_repo: Path):
    _run_in(node_repo, ["adopt"])
    result = _run_in(node_repo, ["export"])
    assert result.exit_code == 0
    export_dir = node_repo / ".dist-release" / node_repo.name
    assert export_dir.exists()
    assert not (export_dir / ".ai-workflow").exists()
    assert (export_dir / "package.json").exists()


def test_release_creates_notes_and_clean_export(node_repo: Path):
    _run_in(node_repo, ["adopt"])
    result = _run_in(node_repo, ["release", "--version", "0.3.0", "--skip-build"])
    assert result.exit_code == 0
    release_dir = node_repo / ".dist-release" / "releases" / "v0.3.0"
    assert (release_dir / "repo").exists()
    assert (release_dir / "RELEASE_NOTES.md").exists()
    assert not (release_dir / "repo" / ".ai-workflow").exists()


def test_completion_command_outputs_shell_snippet(git_repo: Path):
    result = _run_in(git_repo, ["completion", "zsh"])
    assert result.exit_code == 0
    assert "_AWF_COMPLETE=zsh_source awf" in result.stdout


def test_hooks_install_writes_git_hooks_and_precommit(git_repo: Path):
    result = _run_in(git_repo, ["hooks", "--with-pre-commit"])
    assert result.exit_code == 0
    assert (git_repo / ".git" / "hooks" / "post-checkout").exists()
    assert (git_repo / ".git" / "hooks" / "post-merge").exists()
    assert (git_repo / ".git" / "hooks" / "pre-commit").exists()
    assert (git_repo / ".pre-commit-config.yaml").exists()
