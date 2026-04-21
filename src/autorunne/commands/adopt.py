from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root, ensure_local_exclude
from autorunne.core.paths import save_config, view_file
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.state_engine import bootstrap_workspace, record_integration
from autorunne.core.integrations import install_integrations
from autorunne.core.vscode import install_vscode_integration
from autorunne.models.config import WorkflowConfig


def run(target: Path, with_vscode: bool = False) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne adopt must run inside an existing git repository")
    scan = scan_repo(repo_root)
    scan["next_action"] = recommend_next_action(scan)
    bootstrap_workspace(repo_root, scan, action="workspace_adopted")
    save_config(repo_root, WorkflowConfig())
    exclude_path = ensure_local_exclude(repo_root)
    integration = install_integrations(repo_root, tool="all", scope="repo")
    record_integration(repo_root, scope="repo", tools=integration["tools"], wrappers=integration["wrappers"], action="integration_installed")
    result = {
        "repo_root": str(repo_root),
        "exclude_path": str(exclude_path),
        "scan": scan,
        "start_here_path": str(view_file(repo_root, "START_HERE.md")),
        "integration": integration,
    }
    if with_vscode:
        result["vscode"] = install_vscode_integration(repo_root)
    return result
