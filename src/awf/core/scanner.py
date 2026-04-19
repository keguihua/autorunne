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
    "go.mod",
    "Cargo.toml",
]

SOURCE_DIR_CANDIDATES = {"src", "app", "server", "backend", "frontend", "tests", "cmd", "internal"}


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").lower() if path.exists() else ""


def _detect_node(repo_root: Path, scan: dict) -> None:
    package_json_path = repo_root / "package.json"
    if not package_json_path.exists():
        return

    package_json = _safe_read_json(package_json_path)
    scripts = package_json.get("scripts", {})
    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

    scan["stack"].append("node")
    if (repo_root / "pnpm-lock.yaml").exists():
        package_manager = "pnpm"
    elif (repo_root / "yarn.lock").exists():
        package_manager = "yarn"
    elif (repo_root / "bun.lockb").exists() or (repo_root / "bun.lock").exists():
        package_manager = "bun"
    else:
        package_manager = "npm"
    scan["package_manager"].append(package_manager)

    framework_map = {
        "next": "nextjs",
        "react": "react",
        "vite": "vite",
        "nuxt": "nuxt",
        "vue": "vue",
        "svelte": "svelte",
        "@sveltejs/kit": "sveltekit",
        "express": "express",
        "nestjs": "nestjs",
    }
    for dep, name in framework_map.items():
        if dep in deps and name not in scan["framework"]:
            scan["framework"].append(name)

    if scripts.get("test"):
        scan["commands"]["test"] = f"{package_manager} test"
    elif scripts.get("lint"):
        scan["commands"]["test"] = f"{package_manager} run lint"
    if scripts.get("dev"):
        scan["commands"]["run"] = f"{package_manager} run dev"
    if scripts.get("build"):
        scan["commands"]["build"] = f"{package_manager} run build"


def _detect_python(repo_root: Path, scan: dict) -> None:
    pyproject_path = repo_root / "pyproject.toml"
    requirements_path = repo_root / "requirements.txt"
    if not pyproject_path.exists() and not requirements_path.exists():
        return

    scan["stack"].append("python")
    pyproject_text = _read_text(pyproject_path)
    requirements_text = _read_text(requirements_path)
    combined = pyproject_text + "\n" + requirements_text

    framework_tokens = {
        "fastapi": "fastapi",
        "django": "django",
        "flask": "flask",
        "streamlit": "streamlit",
    }
    for token, name in framework_tokens.items():
        if token in combined and name not in scan["framework"]:
            scan["framework"].append(name)

    if "poetry" in pyproject_text:
        scan["package_manager"].append("poetry")
    elif "uv" in pyproject_text:
        scan["package_manager"].append("uv")
    else:
        scan["package_manager"].append("pip")

    if "pytest" in combined or (repo_root / "tests").exists():
        scan["commands"].setdefault("test", "pytest")
    else:
        scan["commands"].setdefault("test", "python -m unittest")
    scan["commands"].setdefault("run", "python -m <entrypoint>")


def _detect_go(repo_root: Path, scan: dict) -> None:
    if not (repo_root / "go.mod").exists():
        return
    scan["stack"].append("go")
    scan["framework"].append("go")
    scan["package_manager"].append("go")
    scan["commands"].setdefault("run", "go run .")
    scan["commands"].setdefault("test", "go test ./...")
    scan["commands"].setdefault("build", "go build ./...")


def _detect_rust(repo_root: Path, scan: dict) -> None:
    if not (repo_root / "Cargo.toml").exists():
        return
    scan["stack"].append("rust")
    scan["framework"].append("rust")
    scan["package_manager"].append("cargo")
    scan["commands"].setdefault("run", "cargo run")
    scan["commands"].setdefault("test", "cargo test")
    scan["commands"].setdefault("build", "cargo build")



def _unique(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered



def scan_repo(repo_root: Path) -> dict:
    files = {path.name: path for path in repo_root.iterdir() if path.is_file()}
    dirs = sorted(path.name for path in repo_root.iterdir() if path.is_dir() and not path.name.startswith("."))

    scan = {
        "repo_name": repo_root.name,
        "stack": [],
        "framework": [],
        "package_manager": [],
        "important_files": [],
        "source_dirs": [],
        "commands": {},
        "dirs": dirs,
    }

    _detect_node(repo_root, scan)
    _detect_python(repo_root, scan)
    _detect_go(repo_root, scan)
    _detect_rust(repo_root, scan)

    scan["stack"] = _unique(scan["stack"]) or ["generic"]
    scan["framework"] = _unique(scan["framework"]) or ["generic"]
    scan["package_manager"] = _unique(scan["package_manager"]) or ["unknown"]

    scan["important_files"] = [name for name in IMPORTANT_FILES if name in files]
    scan["source_dirs"] = [name for name in dirs if name in SOURCE_DIR_CANDIDATES]
    return scan



def recommend_next_action(scan: dict) -> str:
    if "README.md" not in scan.get("important_files", []):
        return "Create or improve the project README so both humans and agents know how to run the project."
    if scan.get("commands", {}).get("test") == "pytest":
        return "Run the Python test command and record any failing modules before changing code."
    if "node" in scan.get("stack", []):
        return "Confirm the package manager and run the main test or lint command before touching code."
    if "go" in scan.get("stack", []):
        return "Run the Go test command first, then map the smallest safe next change."
    return "Validate the local run/test commands, then choose the smallest next task from TASKS.md."
