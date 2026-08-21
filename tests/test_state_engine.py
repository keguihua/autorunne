from __future__ import annotations

import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from autorunne import __version__
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


def test_finish_keeps_session_log_validation_output_concise_and_status_visible(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    long_script = "for i in range(30): print('line %s' % i)"

    result = _run_in(
        python_repo,
        [
            "finish",
            "--summary",
            "Recorded concise validation",
            "--validate",
            f'python -c "{long_script}"',
            "--next",
            "Continue product slice",
        ],
    )
    assert result.exit_code == 0

    session_log = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    status = (python_repo / ".autorunne" / "views" / "STATUS.md").read_text(encoding="utf-8")
    assert "Validation command:" in session_log
    assert "validation_output:" in session_log
    assert "line 0" in session_log
    assert "line 29" not in session_log
    assert "more lines omitted" in session_log
    assert "验证命令：`python -c" in status
    assert "验证结果摘要：line 0" in status


def test_repeated_open_does_not_duplicate_identical_resume_or_integration_logs(python_repo: Path):
    _run_in(python_repo, ["open"])
    _run_in(python_repo, ["open"])

    # Simulate a real agent handoff where an integration refresh/noise entry can
    # sit between two otherwise identical open auto-resume events. Existing
    # repo-local agent skill files should not be silently rewritten by open.
    skill_path = python_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md"
    older_skill_text = skill_path.read_text(encoding="utf-8").replace(f"version: {__version__}", "version: 0.6.0")
    skill_path.write_text(older_skill_text, encoding="utf-8")
    _run_in(python_repo, ["open"])
    _run_in(python_repo, ["open"])

    log_text = (python_repo / ".autorunne" / "SESSION_LOG.md").read_text(encoding="utf-8")
    assert log_text.count("| workspace open auto-resume") == 1
    assert log_text.count("integration updated") <= 1
    assert skill_path.read_text(encoding="utf-8") == older_skill_text


def test_finish_handoff_uses_one_product_next_action_for_new_agents(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    _run_in(
        python_repo,
        [
            "start",
            "--task",
            "Lesson 09/10 real development",
            "--next",
            "Old Lesson 08 workflow note",
        ],
    )
    _run_in(python_repo, ["task", "add", "--text", "Lesson 11 mobile polish"])

    result = _run_in(
        python_repo,
        [
            "finish",
            "--summary",
            "Lesson 09/10 completed",
            "--task",
            "Lesson 09/10",
            "--validate",
            "pytest -q",
            "--next",
            "Lesson 11 mobile polish",
        ],
    )
    assert result.exit_code == 0

    state_root = python_repo / ".autorunne" / "state"
    views_root = python_repo / ".autorunne" / "views"
    current = json.loads((state_root / "current.json").read_text(encoding="utf-8"))
    tasks = json.loads((state_root / "tasks.json").read_text(encoding="utf-8"))
    events = [json.loads(line) for line in (state_root / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    start_here = (views_root / "START_HERE.md").read_text(encoding="utf-8")
    next_action = (views_root / "NEXT_ACTION.md").read_text(encoding="utf-8")
    status_result = _run_in(python_repo, ["status"])

    assert current["active_task"] is None
    assert current["last_action"] == "task_finished"
    assert current["next_action"] == "Lesson 11 mobile polish"
    assert current["next_product_task"] == "Lesson 11 mobile polish"
    assert tasks["next_up"][0]["text"] == "Lesson 11 mobile polish"
    assert current["last_validation"]["command"] == "pytest -q"
    assert current["last_validation"]["status"] == "passed"
    assert current["last_validation"]["timestamp"]
    assert "task_finished" in [event["type"] for event in events]
    assert "Next product task：Lesson 11 mobile polish" in start_here
    assert "- 下一步：Lesson 11 mobile polish" in start_here
    assert "- Next action: Lesson 11 mobile polish" in start_here
    assert "## Next product task\nLesson 11 mobile polish" in next_action
    assert "## Legacy combined next action\nLesson 11 mobile polish" in next_action
    assert status_result.exit_code == 0
    assert "Next action" in status_result.stdout
    assert "Lesson 11 mobile polish" in status_result.stdout


def test_finish_workflow_follow_up_does_not_override_product_next_action(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    _run_in(python_repo, ["start", "--task", "Lesson 09/10 real development", "--next", "Lesson 11 mobile polish"])

    result = _run_in(
        python_repo,
        [
            "finish",
            "--summary",
            "Lesson 09/10 completed",
            "--task",
            "Lesson 09/10",
            "--no-validate",
            "--next",
            "Workflow follow-up: review rendered STATUS and START_HERE",
        ],
    )
    assert result.exit_code == 0

    current = json.loads((python_repo / ".autorunne" / "state" / "current.json").read_text(encoding="utf-8"))
    start_here = (python_repo / ".autorunne" / "views" / "START_HERE.md").read_text(encoding="utf-8")
    assert current["next_action"] == "Lesson 11 mobile polish"
    assert current["next_product_task"] == "Lesson 11 mobile polish"
    assert current["workflow_follow_up"] == "Workflow follow-up: review rendered STATUS and START_HERE"
    assert "- 下一步：Lesson 11 mobile polish" in start_here
    assert "Workflow follow-up：Workflow follow-up: review rendered STATUS and START_HERE" in start_here



def test_sync_cleans_stale_workflow_follow_up_from_main_backlog_after_finish(python_repo: Path):
    _run_in(python_repo, ["adopt"])

    state_root = python_repo / ".autorunne" / "state"
    current_path = state_root / "current.json"
    tasks_path = state_root / "tasks.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    stale_workflow = "Old Lesson 08 workflow follow-up: review START_HERE status view"
    current["next_action"] = stale_workflow
    current["next_product_task"] = stale_workflow
    current["workflow_follow_up"] = stale_workflow
    tasks["next_up"] = [{"text": stale_workflow, "status": "pending", "timestamp": "old", "source": "legacy-sync"}]
    tasks["in_progress"] = [{"text": "Lesson 09/10 real development", "status": "pending", "timestamp": "old", "source": "legacy"}]
    current["active_task"] = "Lesson 09/10 real development"
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    _run_in(python_repo, ["task", "add", "--text", "Lesson 11 mobile polish"])
    finish = _run_in(
        python_repo,
        [
            "finish",
            "--summary",
            "Lesson 09/10 completed",
            "--task",
            "Lesson 09/10",
            "--no-validate",
            "--next",
            "Lesson 11 mobile polish",
        ],
    )
    assert finish.exit_code == 0
    sync = _run_in(python_repo, ["sync"])
    assert sync.exit_code == 0

    current = json.loads(current_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    start_here = (python_repo / ".autorunne" / "views" / "START_HERE.md").read_text(encoding="utf-8")
    next_action = (python_repo / ".autorunne" / "views" / "NEXT_ACTION.md").read_text(encoding="utf-8")
    status = _run_in(python_repo, ["status"])

    assert current["next_action"] == "Lesson 11 mobile polish"
    assert current["next_product_task"] == "Lesson 11 mobile polish"
    assert current["workflow_follow_up"] == "无"
    assert tasks["next_up"][0]["text"] == "Lesson 11 mobile polish"
    assert stale_workflow not in [item["text"] for item in tasks["next_up"]]
    assert "- 下一步：Lesson 11 mobile polish" in start_here
    assert "- Next action: Lesson 11 mobile polish" in start_here
    assert "## Legacy combined next action\nLesson 11 mobile polish" in next_action
    assert status.exit_code == 0
    assert "Lesson 11 mobile polish" in status.stdout


def test_doctor_reports_handoff_consistency_drift(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    current_path = python_repo / ".autorunne" / "state" / "current.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    current["next_action"] = "Old Lesson 08 workflow follow-up"
    current["next_product_task"] = "Lesson 11 mobile polish"
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = _run_in(python_repo, ["doctor"])

    assert result.exit_code == 1
    assert "handoff_consistency" in result.stdout
    assert "current.next_action" in result.stdout
    assert "current.next_product_task" in result.stdout


def test_repair_handoff_realigns_legacy_state_and_views(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    state_root = python_repo / ".autorunne" / "state"
    current_path = state_root / "current.json"
    tasks_path = state_root / "tasks.json"
    current = json.loads(current_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    old_workflow = "Old Lesson 08 workflow follow-up: review STATUS.md"
    current["next_action"] = old_workflow
    current["next_product_task"] = "Lesson 11 mobile polish"
    current["workflow_follow_up"] = old_workflow
    tasks["next_up"] = [
        {"text": old_workflow, "status": "pending", "timestamp": "old", "source": "legacy-sync"},
        {"text": "Lesson 11 mobile polish", "status": "pending", "timestamp": "old", "source": "finish"},
    ]
    current_path.write_text(json.dumps(current, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tasks_path.write_text(json.dumps(tasks, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    result = _run_in(python_repo, ["repair-handoff"])

    assert result.exit_code == 0
    current = json.loads(current_path.read_text(encoding="utf-8"))
    tasks = json.loads(tasks_path.read_text(encoding="utf-8"))
    start_here = (python_repo / ".autorunne" / "views" / "START_HERE.md").read_text(encoding="utf-8")
    assert current["next_action"] == "Lesson 11 mobile polish"
    assert current["next_product_task"] == "Lesson 11 mobile polish"
    assert tasks["next_up"][0]["text"] == "Lesson 11 mobile polish"
    assert old_workflow not in [item["text"] for item in tasks["next_up"]]
    assert "- 下一步：Lesson 11 mobile polish" in start_here


def test_finish_changed_files_are_classified_and_keep_integration_out_of_business(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    (python_repo / "src" / "app.py").write_text("print('business change')\n", encoding="utf-8")
    skill_path = python_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md"
    skill_path.write_text(skill_path.read_text(encoding="utf-8").replace("version:", "version: # dirty\nold-version:"), encoding="utf-8")

    result = _run_in(python_repo, ["finish", "--summary", "Classified files", "--no-validate", "--next", "Next product slice"])

    assert result.exit_code == 0
    events = [json.loads(line) for line in (python_repo / ".autorunne" / "state" / "events.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    payload = events[-1]["payload"]
    assert "src/app.py" in payload["changed_files"]
    assert ".agents/skills/autorunne-workflow/SKILL.md" not in payload["changed_files"]
    assert ".agents/skills/autorunne-workflow/SKILL.md" in payload["changed_files_by_type"]["integration"]
    assert "src/app.py" in payload["changed_files_by_type"]["business"]


def test_concurrent_task_add_preserves_every_unique_task(python_repo: Path):
    _run_in(python_repo, ["adopt"])
    env = os.environ.copy()
    env["AUTORUNNE_DISABLE_UPDATE_CHECK"] = "1"
    autorunne_bin = str(Path(sys.prefix) / "bin" / "autorunne")
    texts = [f"concurrent task {index}" for index in range(40)]

    def add_one(text: str) -> int:
        completed = subprocess.run(
            [autorunne_bin, "task", "add", "--text", text, "--path", str(python_repo)],
            env=env,
            capture_output=True,
            text=True,
            check=False,
        )
        return completed.returncode

    with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
        codes = list(pool.map(add_one, texts))

    assert codes == [0] * 40
    expected = {f"concurrent task {index}" for index in range(40)}
    tasks = json.loads((python_repo / ".autorunne/state/tasks.json").read_text())
    assert expected <= {item["text"] for item in tasks["next_up"]}


@pytest.mark.parametrize("command", [["open"], ["doctor", "--handoff"]])
def test_malformed_sessions_recover_from_valid_backup(python_repo: Path, command: list[str]):
    _run_in(python_repo, ["adopt"])
    _run_in(python_repo, ["sync"])
    sessions = python_repo / ".autorunne" / "state" / "sessions.json"
    backup = sessions.with_name("sessions.json.bak")
    assert backup.exists()
    sessions.write_text("{", encoding="utf-8")
    result = _run_in(python_repo, command)
    assert result.exit_code == 0
    json.loads(sessions.read_text(encoding="utf-8"))


@pytest.mark.parametrize("command", [["open"], ["doctor", "--handoff"]])
def test_unrecoverable_sessions_fail_closed_without_overwrite(python_repo: Path, command: list[str]):
    _run_in(python_repo, ["adopt"])
    sessions = python_repo / ".autorunne" / "state" / "sessions.json"
    backup = sessions.with_name("sessions.json.bak")
    sessions.write_text("{", encoding="utf-8")
    backup.write_text("[", encoding="utf-8")
    result = _run_in(python_repo, command)
    combined = f"{result.stdout}{result.stderr}"
    assert result.exit_code == 1
    assert "Autorunne state is corrupt" in combined
    assert "did not reset state" in combined
    assert sessions.read_text(encoding="utf-8") == "{"
    assert backup.read_text(encoding="utf-8") == "["
