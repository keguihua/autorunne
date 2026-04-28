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
    agents_skill = (git_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").read_text(encoding="utf-8")
    claude_skill = (git_repo / ".claude" / "skills" / "autorunne-workflow" / "SKILL.md").read_text(encoding="utf-8")
    cursor_rule = (git_repo / ".cursor" / "rules" / "autorunne-workflow.mdc").read_text(encoding="utf-8")
    assert agents_skill.startswith("---\n")
    assert "name: autorunne-workflow" in agents_skill
    assert claude_skill.startswith("---\n")
    assert "version: 0.6.9" in claude_skill
    assert "open Codex directly" in agents_skill
    assert "autorunne ingest --source codex --task <task>" in agents_skill
    assert cursor_rule.startswith("---\n")
    assert "alwaysApply: true" in cursor_rule
    assert "globs:" not in cursor_rule


def test_open_auto_installs_repo_integrations(node_repo: Path):
    result = _run_in(node_repo, ["open"])
    assert result.exit_code == 0
    assert (node_repo / "AGENTS.md").exists()
    assert (node_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (node_repo / ".claude" / "skills" / "autorunne-workflow" / "SKILL.md").exists()
    assert (node_repo / ".cursor" / "rules" / "autorunne-workflow.mdc").exists()
    assert (node_repo / ".github" / "copilot-instructions.md").exists()
    assert (node_repo / ".autorunne" / "bin" / "ar-codex").exists()
    skill_text = (node_repo / ".agents" / "skills" / "autorunne-workflow" / "SKILL.md").read_text(encoding="utf-8")
    assert skill_text.startswith("---\n")
