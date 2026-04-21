from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root
from autorunne.core.integrations import install_integrations
from autorunne.core.scanner import recommend_next_action, scan_repo
from autorunne.core.state_engine import bootstrap_workspace, record_integration, workflow_exists


def run(target: Path, *, tool: str = "all", scope: str = "repo") -> dict:
    repo_root = detect_repo_root(target) or target
    if scope == "repo" and not (repo_root / ".git").exists():
        raise RuntimeError("autorunne integrate --scope repo must run inside an existing git repository")
    if scope == "repo" and not workflow_exists(repo_root):
        scan = scan_repo(repo_root)
        scan["next_action"] = recommend_next_action(scan)
        bootstrap_workspace(repo_root, scan, action="workspace_bootstrapped", note="bootstrap for repo integration install")
    result = install_integrations(repo_root, tool=tool, scope=scope)
    if scope == "repo":
        record_integration(repo_root, scope=scope, tools=result["tools"], wrappers=result["wrappers"], action="integration_updated")
    return result
