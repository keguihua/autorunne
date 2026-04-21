from __future__ import annotations

from pathlib import Path

from autorunne.commands import adopt as adopt_cmd
from autorunne.commands import sync as sync_cmd
from autorunne.core.gitops import detect_repo_root
from autorunne.core.paths import workflow_file, workflow_dir
from autorunne.core.vscode import install_vscode_integration


def run(target: Path, with_vscode: bool = False) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne open must run inside an existing git repository")

    workflow_exists = workflow_dir(repo_root).exists()
    if workflow_exists:
        result = sync_cmd.run(repo_root, note="workspace open auto-resume")
        action = "resumed"
    else:
        result = adopt_cmd.run(repo_root, with_vscode=False)
        action = "bootstrapped"

    vscode_result = None
    if with_vscode:
        vscode_result = install_vscode_integration(repo_root)

    return {
        "action": action,
        "repo_root": str(repo_root),
        "scan": result["scan"],
        "start_here_path": str(workflow_file(repo_root, "START_HERE.md")),
        "workflow_exists": workflow_exists,
        "vscode": vscode_result,
    }
