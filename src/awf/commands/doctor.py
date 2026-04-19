from __future__ import annotations

from pathlib import Path

from awf.core.gitops import detect_repo_root, is_tracked
from awf.core.paths import workflow_dir

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
    result = {
        "repo_root": str(repo_root),
        "is_git_repo": (repo_root / ".git").exists(),
        "workflow_exists": workflow_dir(repo_root).exists(),
        "missing": [],
        "warnings": [],
    }
    if not result["is_git_repo"]:
        result["warnings"].append("Not inside a git repository")
        return result
    root = workflow_dir(repo_root)
    if root.exists():
        result["missing"] = [name for name in EXPECTED_FILES if not (root / name).exists()]
        if is_tracked(repo_root, root.name):
            result["warnings"].append(".ai-workflow is tracked by git; keep it local-only")
    else:
        result["warnings"].append("Workflow directory does not exist yet")
    exclude_path = repo_root / ".git" / "info" / "exclude"
    if not exclude_path.exists() or ".ai-workflow/" not in exclude_path.read_text(encoding="utf-8"):
        result["warnings"].append(".git/info/exclude does not contain .ai-workflow/")
    return result
