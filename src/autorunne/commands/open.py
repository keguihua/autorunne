from __future__ import annotations

from pathlib import Path

from autorunne.commands import adopt as adopt_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import view_file
from autorunne.core.integrations import install_integrations
from autorunne.core.state_engine import record_integration, workflow_exists
from autorunne.core.vscode import install_vscode_integration


def run(target: Path, with_vscode: bool = False) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne open must run inside an existing git repository")

    existing = workflow_exists(repo_root)
    if existing:
        result = sync_cmd.run(repo_root, note="workspace open auto-resume", action="workspace_resumed")
        action = "resumed"
    else:
        result = adopt_cmd.run(repo_root, with_vscode=False)
        action = "bootstrapped"

    integration = install_integrations(repo_root, tool="all", scope="repo")
    record_integration(repo_root, scope="repo", tools=integration["tools"], wrappers=integration["wrappers"], action="integration_updated" if existing else "integration_installed")

    vscode_result = None
    if with_vscode:
        vscode_result = install_vscode_integration(repo_root)

    return {
        "action": action,
        "repo_root": str(repo_root),
        "scan": result["scan"],
        "start_here_path": str(view_file(repo_root, "START_HERE.md")),
        "workflow_exists": existing,
        "vscode": vscode_result,
        "integration": integration,
    }
