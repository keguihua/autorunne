from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root, is_tracked
from autorunne.core.paths import workflow_dir

EXPECTED_FILES = [
    "PROJECT_CONTEXT.md",
    "TASKS.md",
    "DECISIONS.md",
    "SESSION_LOG.md",
    "RULES.md",
    "NEXT_ACTION.md",
    "config.json",
]


def run(target: Path) -> dict:
    repo_root = detect_repo_root(target) or target
    root = workflow_dir(repo_root)
    exclude_path = repo_root / ".git" / "info" / "exclude"
    vscode_settings = repo_root / ".vscode" / "settings.json"
    vscode_tasks = repo_root / ".vscode" / "tasks.json"
    post_checkout = repo_root / ".git" / "hooks" / "post-checkout"
    post_merge = repo_root / ".git" / "hooks" / "post-merge"
    pre_commit_hook = repo_root / ".git" / "hooks" / "pre-commit"
    precommit_config = repo_root / ".pre-commit-config.yaml"

    result = {
        "repo_root": str(repo_root),
        "is_git_repo": (repo_root / ".git").exists(),
        "workflow_exists": root.exists(),
        "missing": [],
        "warnings": [],
        "checks": {},
    }
    if not result["is_git_repo"]:
        result["warnings"].append("Not inside a git repository")
        result["checks"]["git_repo"] = "missing"
        return result

    result["checks"]["git_repo"] = "ok"

    if root.exists():
        result["missing"] = [name for name in EXPECTED_FILES if not (root / name).exists()]
        result["checks"]["workflow_files"] = "ok" if not result["missing"] else "missing"
        if is_tracked(repo_root, root.name):
            result["warnings"].append(".autorunne is tracked by git; keep it local-only")
    else:
        result["warnings"].append("Autorunne workspace does not exist yet")
        result["checks"]["workflow_files"] = "missing"

    if not exclude_path.exists() or ".autorunne/" not in exclude_path.read_text(encoding="utf-8"):
        result["warnings"].append(".git/info/exclude does not contain .autorunne/")
        result["checks"]["git_exclude"] = "missing"
    else:
        result["checks"]["git_exclude"] = "ok"

    hooks_ok = post_checkout.exists() and post_merge.exists()
    if not hooks_ok:
        result["warnings"].append("Git hooks are not installed")
        result["checks"]["hooks"] = "missing"
    else:
        result["checks"]["hooks"] = "ok"

    vscode_ok = vscode_settings.exists() and vscode_tasks.exists()
    result["checks"]["vscode"] = "ok" if vscode_ok else "missing"

    precommit_ok = pre_commit_hook.exists() and precommit_config.exists()
    if not precommit_ok:
        result["warnings"].append("Pre-commit config is not installed")
        result["checks"]["pre_commit"] = "missing"
    else:
        result["checks"]["pre_commit"] = "ok"

    dist_dir = repo_root / "dist"
    result["checks"]["package_artifacts"] = "ok" if dist_dir.exists() and any(dist_dir.iterdir()) else "missing"

    return result
