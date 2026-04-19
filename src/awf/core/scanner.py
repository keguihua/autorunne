from __future__ import annotations

import json
from pathlib import Path


IMPORTANT_FILES = [
    "README.md",
    "package.json",
    "pyproject.toml",
    "requirements.txt",
    "Dockerfile",
    ".env.example",
]


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def scan_repo(repo_root: Path) -> dict:
    files = {path.name: path for path in repo_root.iterdir() if path.is_file()}
    dirs = sorted(path.name for path in repo_root.iterdir() if path.is_dir() and not path.name.startswith("."))

    package_json = _safe_read_json(repo_root / "package.json") if (repo_root / "package.json").exists() else {}

    stack = []
    framework = []
    package_manager = []
    commands: dict[str, str] = {}

    if (repo_root / "package.json").exists():
        stack.append("node")
        scripts = package_json.get("scripts", {})
        deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}
        if (repo_root / "pnpm-lock.yaml").exists():
            package_manager.append("pnpm")
        elif (repo_root / "yarn.lock").exists():
            package_manager.append("yarn")
        elif (repo_root / "bun.lockb").exists() or (repo_root / "bun.lock").exists():
            package_manager.append("bun")
        else:
            package_manager.append("npm")
        if "next" in deps:
            framework.append("nextjs")
        if "react" in deps and "next" not in deps:
            framework.append("react")
        if "vite" in deps:
            framework.append("vite")
        if scripts.get("test"):
            commands["test"] = f"{package_manager[0]} test"
        elif scripts.get("lint"):
            commands["test"] = f"{package_manager[0]} run lint"
        if scripts.get("dev"):
            commands["run"] = f"{package_manager[0]} run dev"

    if (repo_root / "pyproject.toml").exists() or (repo_root / "requirements.txt").exists():
        stack.append("python")
        if (repo_root / "pyproject.toml").exists():
            pyproject = (repo_root / "pyproject.toml").read_text(encoding="utf-8", errors="ignore").lower()
            if "fastapi" in pyproject:
                framework.append("fastapi")
            if "django" in pyproject:
                framework.append("django")
            if "flask" in pyproject:
                framework.append("flask")
            if "poetry" in pyproject:
                package_manager.append("poetry")
        if not package_manager:
            package_manager.append("pip")
        commands.setdefault("test", "pytest")
        commands.setdefault("run", "python -m <entrypoint>")

    if not stack:
        stack = ["generic"]
    if not framework:
        framework = ["generic"]
    if not package_manager:
        package_manager = ["unknown"]

    important_files = [name for name in IMPORTANT_FILES if name in files]
    source_dirs = [name for name in dirs if name in {"src", "app", "server", "backend", "frontend", "tests"}]

    return {
        "repo_name": repo_root.name,
        "stack": stack,
        "framework": framework,
        "package_manager": package_manager,
        "important_files": important_files,
        "source_dirs": source_dirs,
        "commands": commands,
        "dirs": dirs,
    }


def recommend_next_action(scan: dict) -> str:
    if "README.md" not in scan.get("important_files", []):
        return "Create or improve the project README so both humans and agents know how to run the project."
    if scan.get("commands", {}).get("test") == "pytest":
        return "Run the Python test command and record any failing modules before changing code."
    if scan.get("stack") == ["node"]:
        return "Confirm the package manager and run the main test or lint command before touching code."
    return "Validate the local run/test commands, then choose the smallest next task from TASKS.md."
