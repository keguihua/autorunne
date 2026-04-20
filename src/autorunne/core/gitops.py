from __future__ import annotations

import subprocess
from pathlib import Path


class GitError(RuntimeError):
    pass


def _run_git(repo_root: Path, args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        ["git", *args],
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if check and result.returncode != 0:
        raise GitError(result.stderr.strip() or result.stdout.strip() or f"git {' '.join(args)} failed")
    return result


def detect_repo_root(start: Path) -> Path | None:
    result = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=start,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return None
    return Path(result.stdout.strip())


def is_git_repo(start: Path) -> bool:
    return detect_repo_root(start) is not None


def ensure_local_exclude(repo_root: Path, pattern: str = ".autorunne/") -> Path:
    exclude_path = repo_root / ".git" / "info" / "exclude"
    exclude_path.parent.mkdir(parents=True, exist_ok=True)
    if exclude_path.exists():
        lines = exclude_path.read_text(encoding="utf-8").splitlines()
    else:
        lines = []
    normalized = {line.strip() for line in lines if line.strip()}
    if pattern not in normalized:
        lines.append(pattern)
        exclude_path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    return exclude_path


def is_tracked(repo_root: Path, rel_path: str) -> bool:
    result = _run_git(repo_root, ["ls-files", "--error-unmatch", rel_path], check=False)
    return result.returncode == 0


def current_branch(repo_root: Path) -> str | None:
    result = _run_git(repo_root, ["branch", "--show-current"], check=False)
    if result.returncode != 0:
        return None
    return result.stdout.strip() or None
