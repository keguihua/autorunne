import json
import os
import threading
import time
from pathlib import Path

from typer.testing import CliRunner

from autorunne.cli import app
from autorunne import __version__

runner = CliRunner()


def _run_in(repo: Path, args: list[str]):
    old = Path.cwd()
    os.chdir(repo)
    try:
        return runner.invoke(app, args, catch_exceptions=False)
    finally:
        os.chdir(old)


def test_version_command_and_option_print_package_version():
    result = runner.invoke(app, ["version"], catch_exceptions=False)
    assert result.exit_code == 0
    assert f"AutoRunne {__version__}" in result.stdout

    option_result = runner.invoke(app, ["--version"], catch_exceptions=False)
    assert option_result.exit_code == 0
    assert f"AutoRunne {__version__}" in option_result.stdout


def test_self_upgrade_dry_run_uses_public_pypi_no_cache_pipx_command():
    result = runner.invoke(app, ["self-upgrade", "--dry-run"], catch_exceptions=False)
    assert result.exit_code == 0
    assert "pipx upgrade autorunne" in result.stdout
    assert "'--no-cache-dir -i https://pypi.org/simple'" in result.stdout
    assert "does not touch project .autorunne/ directories" in result.stdout


def test_sync_migrates_old_config_version_without_deleting_user_state(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    config_path = python_repo / ".autorunne" / "config.json"
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["version"] = "0.5.0"
    config["preferred_agent"] = "codex"
    config_path.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    preserved_files = [
        python_repo / ".autorunne" / "START_HERE.md",
        python_repo / ".autorunne" / "NEXT_ACTION.md",
        python_repo / ".autorunne" / "TASKS.md",
        python_repo / ".autorunne" / "state" / "current.json",
        python_repo / ".autorunne" / "reports" / "keep.md",
        python_repo / ".autorunne" / "runtime" / "keep.json",
        python_repo / ".autorunne" / "skills" / "keep.md",
    ]
    for path in preserved_files:
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            path.write_text("keep\n", encoding="utf-8")

    result = _run_in(python_repo, ["sync"])
    assert result.exit_code == 0

    migrated = json.loads(config_path.read_text(encoding="utf-8"))
    assert migrated["version"] == __version__
    assert migrated["preferred_agent"] == "codex"
    assert migrated["auto_record_on_change"] is True
    for path in preserved_files:
        assert path.exists(), f"expected sync to preserve {path}"


def test_init_creates_workflow_files(git_repo: Path):
    result = _run_in(git_repo, ["init"])
    assert result.exit_code == 0
    workflow_root = git_repo / ".autorunne"
    assert workflow_root.exists()
    assert (workflow_root / "state" / "current.json").exists()
    assert (workflow_root / "state" / "events.jsonl").exists()
    assert (workflow_root / "state" / "tasks.json").exists()
    assert (workflow_root / "state" / "decisions.json").exists()
    assert (workflow_root / "state" / "sessions.json").exists()
    assert (workflow_root / "views" / "START_HERE.md").exists()
    assert (workflow_root / "PROJECT_CONTEXT.md").exists()
    assert (workflow_root / "agents" / "autorunne-workflow.md").exists()
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
    workflow_text = (node_repo / ".autorunne" / "agents" / "autorunne-workflow.md").read_text(encoding="utf-8")
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
    assert "Open Codex / Claude Code / Hermes directly" in start_here_text
    assert "START_HERE.md" in copilot_text
    assert "autorunne-workflow.md" in workflow_text
    assert "completion status" in workflow_text


def test_open_bootstraps_missing_workflow_and_installs_vscode(node_repo: Path):
    result = _run_in(node_repo, ["open", "--with-vscode"])
    assert result.exit_code == 0
    assert "bootstrapped" in result.stdout
    assert (node_repo / ".autorunne" / "START_HERE.md").exists()
    assert (node_repo / ".autorunne" / "views" / "START_HERE.md").exists()
    assert (node_repo / "AGENTS.md").exists()
    assert (node_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    wrapper_text = (node_repo / ".autorunne" / "bin" / "ar-codex").read_text(encoding="utf-8")
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "workflow initialized" in log_text.lower()
    assert "autorunne daemon" in wrapper_text
    assert "autorunne auto-finish --source codex" in wrapper_text
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
        time.sleep(0.5)
        (node_repo / "src" / "index.js").write_text("console.log('daemon changed')\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_file)
    thread.start()
    result = _run_in(node_repo, ["daemon", "--duration", "0.8", "--interval", "0.1"])
    thread.join()
    assert result.exit_code == 0
    assert "Autorunne daemon started from: bootstrapped" in result.stdout
    assert "Auto-syncs:" in result.stdout
    assert "Auto-records:" in result.stdout
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    tasks_text = (node_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    assert "daemon auto-sync" in log_text
    assert "Auto-recorded local changes via daemon" in log_text
    assert "Review and continue the latest local changes in src/index.js" in tasks_text


def test_daemon_reports_changed_files_and_can_stop_after_max_syncs(node_repo: Path):
    def mutate_file_once():
        time.sleep(0.5)
        (node_repo / "src" / "index.js").write_text("console.log('daemon changed once')\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_file_once)
    thread.start()
    result = _run_in(node_repo, ["daemon", "--duration", "2", "--interval", "0.1", "--max-syncs", "1"])
    thread.join()
    assert result.exit_code == 0
    assert "Auto-syncs: 1" in result.stdout
    assert "Last changed files:" in result.stdout
    assert "src/index.js" in result.stdout


def test_daemon_ignores_integration_noise_when_auto_recording(node_repo: Path):
    _run_in(node_repo, ["open"])

    def mutate_noise_only():
        time.sleep(0.2)
        (node_repo / ".codex").write_text("transient codex state\n", encoding="utf-8")

    thread = threading.Thread(target=mutate_noise_only)
    thread.start()
    result = _run_in(node_repo, ["daemon", "--duration", "0.8", "--interval", "0.1", "--max-syncs", "1"])
    thread.join()
    assert result.exit_code == 0
    assert "Auto-syncs: 0" in result.stdout
    assert "Auto-records: 0" in result.stdout
    tasks_text = (node_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "Review and continue the latest local changes in .codex" not in tasks_text
    assert "Auto-recorded local changes via daemon: .codex" not in log_text


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


def test_ingest_captures_direct_codex_task_without_user_chatting_through_autorunne(python_repo: Path):
    result = _run_in(
        python_repo,
        [
            "ingest",
            "--source",
            "codex",
            "--task",
            "Polish onboarding copy",
            "--next",
            "Update docs/onboarding.md with the approved wording",
            "--context",
            "User opened Codex directly in the repo and asked for a copy tweak.",
        ],
    )
    assert result.exit_code == 0
    assert "Task captured from codex: Polish onboarding copy" in result.stdout

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    current_state = json.loads((python_repo / ".autorunne" / "state" / "current.json").read_text(encoding="utf-8"))
    assert "- [ ] Polish onboarding copy" in tasks_text
    assert "Update docs/onboarding.md with the approved wording" in tasks_text
    assert "codex task ingress" in log_text.lower()
    assert "User opened Codex directly in the repo" in log_text
    assert current_state["last_action"] == "codex_task_ingressed"


def test_auto_finish_closes_active_task_after_minimal_docs_change(python_repo: Path):
    _run_in(
        python_repo,
        [
            "hermes-task",
            "--task",
            "Write dogfood note",
            "--next",
            "Use Codex to add the note file",
        ],
    )
    (python_repo / "docs").mkdir()
    (python_repo / "docs" / "dogfood-note.md").write_text("# note\n", encoding="utf-8")

    result = _run_in(python_repo, ["auto-finish", "--source", "codex"])
    assert result.exit_code == 0
    assert "Auto-finished task: Write dogfood note" in result.stdout

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert "[x] Write dogfood note" in tasks_text
    assert "No task in progress right now" in tasks_text
    assert "finish summary" in log_text
    assert "Auto-finished task after codex: Write dogfood note" in log_text


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


def test_status_prefers_explicit_state_over_scan_output(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    _run_in(python_repo, ["start", "--task", "Keep auth stable", "--next", "Custom next step"])

    result = _run_in(python_repo, ["status"])
    assert result.exit_code == 0
    assert "Custom next step" in result.stdout
    assert "Keep auth stable" in result.stdout
    assert "task_started" in result.stdout


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
    state_root = python_repo / ".autorunne" / "state"
    assert log_text != initial_log
    assert "sync summary" in log_text.lower()
    assert "Next action:" in log_text
    assert (state_root / "current.json").exists()
    assert (state_root / "tasks.json").exists()
    assert "No durable decisions recorded yet" in decisions_text
    assert "Keep this manual task" not in tasks_text


def test_start_creates_in_progress_task_and_checkpoint_updates_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    bootstrap_next_action = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8").strip().splitlines()[-1]

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
    assert bootstrap_next_action not in tasks_text
    assert "Write webhook contract tests" not in tasks_text
    assert "start task" in log_text.lower()
    assert "checkpoint" in log_text.lower()
    assert "Mapped webhook payloads" in log_text


def test_finish_replaces_transitional_next_actions_instead_of_accumulating_them(python_repo: Path):
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

    finish_result = _run_in(
        python_repo,
        ["finish", "--summary", "Implemented billing webhook", "--next", "Ship changelog"],
    )
    assert finish_result.exit_code == 0

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    next_action_text = (python_repo / ".autorunne" / "NEXT_ACTION.md").read_text(encoding="utf-8")

    assert "- [x] Implement billing webhook" in tasks_text
    assert "- [ ] Ship changelog" in tasks_text
    assert "Write webhook contract tests" not in tasks_text
    assert "Implement handler wiring" not in tasks_text
    assert "Ship changelog" in next_action_text


def test_start_demotes_stale_in_progress_focus_into_next_up(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    state_root = python_repo / ".autorunne" / "state"
    tasks_state = json.loads((state_root / "tasks.json").read_text(encoding="utf-8"))
    current_state = json.loads((state_root / "current.json").read_text(encoding="utf-8"))
    tasks_state["in_progress"] = [{"text": "Old stale task", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"}]
    tasks_state["next_up"] = [{"text": "Existing queued item", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"}]
    current_state["active_task"] = None
    (state_root / "tasks.json").write_text(json.dumps(tasks_state), encoding="utf-8")
    (state_root / "current.json").write_text(json.dumps(current_state), encoding="utf-8")
    _run_in(python_repo, ["render"])

    start_result = _run_in(
        python_repo,
        ["start", "--task", "Implement billing webhook", "--next", "Write webhook contract tests"],
    )
    assert start_result.exit_code == 0

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    status_result = _run_in(python_repo, ["status"])

    assert "## In progress\n- [ ] Implement billing webhook" in tasks_text
    assert "- [ ] Old stale task" in tasks_text
    assert "- [ ] Existing queued item" in tasks_text
    assert "Active task" in status_result.stdout
    assert "Implement billing webhook" in status_result.stdout


def test_finish_clears_stale_in_progress_when_no_active_task_remains(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    state_root = python_repo / ".autorunne" / "state"
    tasks_state = json.loads((state_root / "tasks.json").read_text(encoding="utf-8"))
    current_state = json.loads((state_root / "current.json").read_text(encoding="utf-8"))
    tasks_state["in_progress"] = [{"text": "Old stale task", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"}]
    tasks_state["next_up"] = [{"text": "Existing queued item", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"}]
    current_state["active_task"] = None
    (state_root / "tasks.json").write_text(json.dumps(tasks_state), encoding="utf-8")
    (state_root / "current.json").write_text(json.dumps(current_state), encoding="utf-8")
    _run_in(python_repo, ["render"])

    finish_result = _run_in(
        python_repo,
        ["finish", "--summary", "Close current slice", "--next", "Ship changelog"],
    )
    assert finish_result.exit_code == 0

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    status_result = _run_in(python_repo, ["status"])

    assert "## In progress\n- [ ] No task in progress right now" in tasks_text
    assert "- [ ] Old stale task" in tasks_text
    assert "- [ ] Ship changelog" in tasks_text
    assert "none" in status_result.stdout.lower()


def test_task_add_in_progress_sets_active_task_and_done_clears_it(python_repo: Path):
    _run_in(python_repo, ["adopt"])

    add_result = _run_in(python_repo, ["task", "add", "--text", "Investigate upgrade path", "--section", "in-progress"])
    assert add_result.exit_code == 0

    status_after_add = _run_in(python_repo, ["status"])
    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    assert "## In progress\n- [ ] Investigate upgrade path" in tasks_text
    assert "Investigate upgrade path" in status_after_add.stdout

    done_result = _run_in(python_repo, ["task", "done", "--match", "Investigate upgrade path", "--section", "in-progress"])
    assert done_result.exit_code == 0

    status_after_done = _run_in(python_repo, ["status"])
    updated_tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    assert "- [x] Investigate upgrade path" in updated_tasks_text
    assert "## In progress\n- [ ] No task in progress right now" in updated_tasks_text
    assert "Active task" in status_after_done.stdout
    assert "none" in status_after_done.stdout.lower()


def test_sync_archives_outdated_release_backlog_into_history_section(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    state_root = python_repo / ".autorunne" / "state"
    tasks_state = json.loads((state_root / "tasks.json").read_text(encoding="utf-8"))
    tasks_state["next_up"] = [
        {"text": "Tag v0.6.3, push GitHub, and verify PyPI release", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"},
        {"text": "Run release verification and publish 0.6.3", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"},
        {"text": "Ship 0.6.5 launch notes", "status": "pending", "timestamp": "2026-01-01 00:00 UTC", "source": "test"},
    ]
    (state_root / "tasks.json").write_text(json.dumps(tasks_state), encoding="utf-8")
    _run_in(python_repo, ["render"])

    sync_result = _run_in(python_repo, ["sync", "--note", "refresh archive candidates"])
    assert sync_result.exit_code == 0

    tasks_text = (python_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    status_result = _run_in(python_repo, ["status"])

    assert "## Archived / historical" in tasks_text
    assert "- [x] Tag v0.6.3, push GitHub, and verify PyPI release" in tasks_text
    assert "- [x] Run release verification and publish 0.6.3" in tasks_text
    assert "- [x] Ship 0.6.5 launch notes" in tasks_text
    assert "archived=" in status_result.stdout


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
    assert "- [x] Implemented auth fix" in tasks_text
    assert "- [ ] Ship release notes" in tasks_text
    assert "Dashboard filters now reuse the shared auth state." in decisions_text
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
    assert "Auto-records: 1" in result.stdout
    log_text = (node_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    tasks_text = (node_repo / ".autorunne" / "TASKS.md").read_text(encoding="utf-8")
    assert "Auto-recorded local changes via watch" in log_text
    assert "Review and continue the latest local changes in src/index.js" in tasks_text


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
    result = _run_in(node_repo, ["release", "--version", "0.6.7", "--skip-build"])
    assert result.exit_code == 0
    release_dir = node_repo / ".dist-release" / "releases" / "v0.6.7"
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
