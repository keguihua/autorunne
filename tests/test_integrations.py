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


def test_integrate_repo_scope_installs_skills_and_wrappers(git_repo: Path):
    result = _run_in(git_repo, ["integrate", "--tool", "all", "--scope", "repo"])
    assert result.exit_code == 0
    assert (git_repo / "AGENTS.md").exists()
    assert (git_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (git_repo / ".claude" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (git_repo / ".cursor" / "rules" / "autorunne-workflow.mdc").exists()
    assert (git_repo / ".github" / "copilot-instructions.md").exists()
    assert (git_repo / ".autorunne" / "state" / "current.json").exists()
    assert (git_repo / ".autorunne" / "bin" / "ar-codex").exists()
    assert (git_repo / ".autorunne" / "bin" / "ar-claude").exists()
    assert (git_repo / ".autorunne" / "bin" / "ar-hermes").exists()


def test_open_auto_installs_repo_integrations(node_repo: Path):
    result = _run_in(node_repo, ["open"])
    assert result.exit_code == 0
    assert (node_repo / "AGENTS.md").exists()
    assert (node_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (node_repo / ".claude" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (node_repo / ".cursor" / "rules" / "autorunne-workflow.mdc").exists()
    assert (node_repo / ".github" / "copilot-instructions.md").exists()
    assert (node_repo / ".autorunne" / "bin" / "ar-codex").exists()
