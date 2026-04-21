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
    commands_text = (node_repo / ".autorunne" / "COMMANDS.md").read_text(encoding="utf-8")
    start_here_text = (node_repo / ".autorunne" / "START_HERE.md").read_text(encoding="utf-8")
    copilot_text = (node_repo / ".autorunne" / "agents" / "copilot.md").read_text(encoding="utf-8")
    assert "Stack: node" in content
    assert "Framework: react, vite" in content
    assert "Project phase:" in content
    assert "Resume hint:" in content
    assert "npm test" in commands_text
    assert "autorunne open" in commands_text
    assert "Claude Code" in start_here_text
    assert "Gemini" in start_here_text
    assert "Hermes" in start_here_text
    assert "Cursor" in start_here_text
    assert "GitHub Copilot" in start_here_text
    assert "Zero-prompt handoff" in start_here_text
    assert "START_HERE.md" in copilot_text


def test_open_bootstraps_missing_workflow_and_installs_vscode(node_repo: Path):
    result = _run_in(node_repo, ["open", "--with-vscode"])
    assert result.exit_code == 0
    assert "bootstrapped" in result.stdout
    assert (node_repo / ".autorunne" / "START_HERE.md").exists()
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "workflow initialized" in log_text.lower()
    tasks = json.loads((node_repo / ".vscode" / "tasks.json").read_text(encoding="utf-8"))
    assert tasks["tasks"][0]["command"] == "autorunne open || python -m autorunne.cli open"


def test_open_resumes_existing_workflow_and_appends_auto_resume_log(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    initial_log = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")

    result = _run_in(python_repo, ["open"])
    assert result.exit_code == 0
    assert "resumed" in result.stdout
    assert "Resume hint:" in result.stdout

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    start_here_text = (python_repo / ".autorunne" / "START_HERE.md").read_text(encoding="utf-8")
    assert log_text != initial_log
    assert "workspace open auto-resume" in log_text
    assert "Zero-prompt handoff" in start_here_text


def test_daemon_bootstraps_then_auto_syncs_on_change(node_repo: Path):
    def mutate_file():
        time.sleep(0.2)
        (node_repo / "src" / "index.js").write_text("console.log('daemon changed')\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_file)
    thread.start()
    result = _run_in(node_repo, ["daemon", "--duration", "0.8", "--interval", "0.1"])
    thread.join()
    assert result.exit_code == 0
    assert "Autorunne daemon started from: bootstrapped" in result.stdout
    assert "Auto-syncs:" in result.stdout
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "daemon auto-sync" in log_text


def test_daemon_reports_changed_files_and_can_stop_after_max_syncs(node_repo: Path):
    def mutate_file_once():
        time.sleep(0.2)
        (node_repo / "src" / "index.js").write_text("console.log('daemon changed once')\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_file_once)
    thread.start()
    result = _run_in(node_repo, ["daemon", "--duration", "2", "--interval", "0.1", "--max-syncs", "1"])
    thread.join()
    assert result.exit_code == 0
    assert "Auto-syncs: 1" in result.stdout
    assert "Last changed files:" in result.stdout
    assert "src/index.js" in result.stdout


def test_hermes_task_bootstraps_repo_and_writes_task_context(python_repo: Path):
    result = _run_in(
        python_repo,
        [
            "hermes-task",
            "--task",
            "Continue billing integration",
            "--next",
            "Write Stripe webhook contract test",
            "--context",
            "User asked Hermes to keep moving on billing without re-explaining the repo.",
            "--decision",
            "Billing work should stay in the smallest safe slice.",
        ],
    )
    assert result.exit_code == 0
    assert "Hermes task captured: Continue billing integration" in result.stdout
    assert "Workspace action:" in result.stdout

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    decisions_text = (python_repo / ".autorunne" / "DECISIONS.md").read_text(encoding="utf-8")
    assert "- [ ] Continue billing integration" in tasks_text
    assert "Write Stripe webhook contract test" in tasks_text
    assert "hermes task ingress" in log_text.lower()
    assert "User asked Hermes" in log_text
    assert "Billing work should stay in the smallest safe slice." in decisions_text


def test_init_can_install_vscode_workspace_integration(git_repo: Path):
    result = _run_in(git_repo, ["init", "--with-vscode"])
    assert result.exit_code == 0
    tasks_path = git_repo / ".vscode" / "tasks.json"
    settings_path = git_repo / ".vscode" / "settings.json"
    assert tasks_path.exists()
    assert settings_path.exists()
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    first_task = tasks["tasks"][0]
    assert first_task["label"] == "Autorunne: Open workspace on folder open"
    assert first_task["command"] == "autorunne open || python -m autorunne.cli open"
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
    decisions_path = python_repo / ".autorunne" / "DECISIONS.md"
    tasks_path = python_repo / ".autorunne" / "TASKS.md"
    decisions_path.write_text(
        decisions_path.read_text(encoding="utf-8") + "\n## Team decisions\n- Keep auth middleware tiny.\n",
        encoding="utf-8",
    )
    tasks_path.write_text(
        tasks_path.read_text(encoding="utf-8") + "\n- [ ] Keep this manual task\n",
        encoding="utf-8",
    )

    result = _run_in(python_repo, ["sync"])
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    decisions_text = decisions_path.read_text(encoding="utf-8")
    tasks_text = tasks_path.read_text(encoding="utf-8")
    assert log_text != initial_log
    assert "sync summary" in log_text.lower()
    assert "Next action:" in log_text
    assert "Keep auth middleware tiny." in decisions_text
    assert "Keep this manual task" in tasks_text


def test_start_creates_in_progress_task_and_checkpoint_updates_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])

    start_result = _run_in(
        python_repo,
        ["start", "--task", "Implement billing webhook", "--next", "Write webhook contract tests"],
    )
    assert start_result.exit_code == 0

    checkpoint_result = _run_in(
        python_repo,
        ["checkpoint", "--summary", "Mapped webhook payloads", "--next", "Implement handler wiring"],
    )
    assert checkpoint_result.exit_code == 0

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")

    assert "- [ ] Implement billing webhook" in tasks_text
    assert "- [ ] Implement handler wiring" in tasks_text
    assert "Implement handler wiring" in next_action_text
    assert "start task" in log_text.lower()
    assert "checkpoint" in log_text.lower()
    assert "Mapped webhook payloads" in log_text


def test_finish_can_run_validation_command_and_record_result(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    result = _run_in(
        python_repo,
        ["finish", "--summary", "Kept tests green", "--validate", "pytest -q", "--next", "Ship changelog"],
    )
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "Validation command: pytest -q" in log_text
    assert "Validation result: passed" in log_text
    assert "Validation: passed" in result.stdout


def test_finish_fails_when_validation_command_fails(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    result = _run_in(
        python_repo,
        ["finish", "--summary", "Tried to finish", "--validate", "python -c \"import sys; sys.exit(1)\""],
    )
    assert result.exit_code == 1
    assert "Validation failed" in result.stdout


def test_finish_appends_summary_and_updates_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    tasks_path = python_repo / ".autorunne" / "TASKS.md"
    tasks_path.write_text(
        "# Tasks\n\n## Completed / inferred\n- Detected stack: python\n\n## In progress\n- [ ] Review dashboard filters\n\n## Next up\n- [ ] Polish billing copy\n\n## Known unknowns\n- [ ] Confirm deployment flow\n",
        encoding="utf-8",
    )
    (python_repo / "src" / "app.py").write_text("print('changed')\n", encoding="utf-8")
    result = _run_in(
        python_repo,
        [
            "finish",
            "--summary",
            "Implemented auth fix",
            "--task",
            "Review dashboard filters",
            "--next",
            "Ship release notes",
            "--decision",
            "Dashboard filters now reuse the shared auth state.",
        ],
    )
    assert result.exit_code == 0

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    tasks_text = tasks_path.read_text(encoding="utf-8")
    decisions_text = (python_repo / ".autorunne" / "DECISIONS.md").read_text(encoding="utf-8")

    assert "finish summary" in log_text.lower()
    assert "Implemented auth fix" in log_text
    assert "Ship release notes" in log_text
    assert "Files changed:" in log_text
    assert "src/app.py" in log_text
    assert "Ship release notes" in next_action_text
    assert "- [x] Review dashboard filters" in tasks_text
    assert "- [ ] Ship release notes" in tasks_text
    assert "- [ ] Polish billing copy" in tasks_text
    assert "Dashboard filters now reuse the shared auth state." in decisions_text
    assert "Matched task:" in result.stdout
    assert "Decision captured:" in result.stdout


def test_finish_without_next_reuses_existing_next_action_and_updates_tasks(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    existing_next_action = next_action_text.strip().splitlines()[-1]

    result = _run_in(python_repo, ["finish", "--summary", "Closed billing edge case"])
    assert result.exit_code == 0

    updated_tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    updated_next_action = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")

    assert "- [x] Closed billing edge case" in updated_tasks_text
    assert f"- [ ] {existing_next_action}" in updated_tasks_text
    assert existing_next_action in updated_next_action


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
    result = _run_in(node_repo, ["release", "--version", "0.6.1", "--skip-build"])
    assert result.exit_code == 0
    release_dir = node_repo / ".dist-release" / "releases" / "v0.6.1"
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
