from __future__ import annotations

import json
import subprocess
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
    "pnpm-workspace.yaml",
    "turbo.json",
    "nx.json",
    "CMakeLists.txt",
    "Makefile",
]

SOURCE_DIR_CANDIDATES = {
    "src",
    "app",
    "server",
    "backend",
    "frontend",
    "contracts",
    "sdk",
    "integrations",
    "tests",
    "cmd",
    "internal",
    "apps",
    "packages",
    "services",
    "include",
}

MONOREPO_PACKAGE_DIRS = ["frontend", "backend", "contracts", "sdk", "integrations"]
MONOREPO_PACKAGE_GLOBS = ["apps/*", "packages/*"]

LOW_SIGNAL_PATH_PREFIXES = (
    ".vscode/",
    ".idea/",
    "dist/",
    ".dist-release/",
    ".pytest_cache/",
    ".mypy_cache/",
)


def _safe_read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="ignore").lower() if path.exists() else ""


def _safe_run(repo_root: Path, args: list[str]) -> str:
    result = subprocess.run(
        args,
        cwd=repo_root,
        text=True,
        capture_output=True,
    )
    if result.returncode != 0:
        return ""
    return result.stdout.strip()


def _normalize_recent_path(candidate: str) -> str:
    trimmed = candidate.strip()
    normalized = trimmed.rstrip("/") or trimmed
    if normalized.startswith("?? ") or normalized.startswith(" M "):
        normalized = normalized[3:].strip()
    return normalized


def _status_candidate(line: str) -> str:
    if len(line) > 3 and line[2] == " ":
        return line[3:].strip()
    if len(line) > 2:
        return line[2:].strip()
    return line.strip()


def _is_low_signal_path(path: str) -> bool:
    normalized = path.strip().rstrip("/")
    return normalized in {".vscode", ".idea", "dist", ".dist-release"} or normalized.startswith(LOW_SIGNAL_PATH_PREFIXES)


def _detect_package_manager(repo_root: Path) -> str:
    if (repo_root / "pnpm-lock.yaml").exists() or (repo_root / "pnpm-workspace.yaml").exists():
        return "pnpm"
    if (repo_root / "yarn.lock").exists():
        return "yarn"
    if (repo_root / "bun.lockb").exists() or (repo_root / "bun.lock").exists():
        return "bun"
    return "npm"


def _script_command(package_path: str, script_name: str, package_manager: str = "npm") -> str:
    prefix = f"cd {package_path} && " if package_path != "." else ""
    if script_name == "test":
        return f"{prefix}{package_manager} test"
    if script_name == "start":
        return f"{prefix}{package_manager} start"
    return f"{prefix}{package_manager} run {script_name}"


def _infer_package_type(package_dir: Path, package_json: dict) -> str:
    scripts = package_json.get("scripts", {}) or {}
    deps = {**(package_json.get("dependencies", {}) or {}), **(package_json.get("devDependencies", {}) or {})}
    script_blob = "\n".join(str(value).lower() for value in scripts.values())
    dep_names = {str(name).lower() for name in deps}
    combined = "\n".join([script_blob, "\n".join(dep_names)])

    if "vite" in combined:
        return "Vite frontend"
    if "hardhat" in combined:
        return "Hardhat smart contracts"
    if (package_dir / "server.js").exists() or "express" in dep_names or "nodemon" in dep_names or "node --test" in script_blob:
        return "Node.js backend"
    return "Node.js package"


def _find_package_jsons(repo_root: Path) -> list[Path]:
    package_paths: list[Path] = []
    for dirname in MONOREPO_PACKAGE_DIRS:
        candidate = repo_root / dirname / "package.json"
        if candidate.exists():
            package_paths.append(candidate)
    for pattern in MONOREPO_PACKAGE_GLOBS:
        for package_dir in sorted(repo_root.glob(pattern)):
            candidate = package_dir / "package.json"
            if candidate.exists() and candidate not in package_paths:
                package_paths.append(candidate)
    return package_paths


def _detect_multi_package_node(repo_root: Path, scan: dict) -> None:
    package_json_paths = _find_package_jsons(repo_root)
    if len(package_json_paths) < 2:
        return

    root_package_manager = _detect_package_manager(repo_root)
    package_manager = f"{root_package_manager} per package"
    packages = []
    frameworks = []
    commands = {}
    source_dirs = []
    important_files = []

    for package_json_path in package_json_paths:
        package_dir = package_json_path.parent
        relative_path = package_dir.relative_to(repo_root).as_posix()
        package_json = _safe_read_json(package_json_path)
        scripts = package_json.get("scripts", {}) or {}
        dependencies = package_json.get("dependencies", {}) or {}
        dev_dependencies = package_json.get("devDependencies", {}) or {}
        package_type = _infer_package_type(package_dir, package_json)
        frameworks.append(package_type)
        source_dirs.append(relative_path)
        important_files.append(f"{relative_path}/package.json")
        packages.append(
            {
                "path": relative_path,
                "name": package_json.get("name") or relative_path,
                "type": package_type,
                "scripts": scripts,
                "dependencies": dependencies,
                "devDependencies": dev_dependencies,
                "package_manager": root_package_manager,
            }
        )
        for script_name in scripts:
            commands[f"{relative_path}:{script_name}"] = _script_command(relative_path, script_name, root_package_manager)

    scan["stack"] = ["multi-package Node/TypeScript"]
    scan["framework"] = _unique(frameworks)
    scan["package_manager"] = [package_manager]
    scan["packages"] = packages
    scan["source_dirs"] = _unique([*source_dirs, *scan.get("source_dirs", [])])
    scan["important_files"] = _unique([*important_files, *scan.get("important_files", [])])
    scan["commands"] = commands


def _detect_node(repo_root: Path, scan: dict) -> None:
    package_json_path = repo_root / "package.json"
    if not package_json_path.exists():
        _detect_multi_package_node(repo_root, scan)
        return

    package_json = _safe_read_json(package_json_path)
    scripts = package_json.get("scripts", {})
    deps = {**package_json.get("dependencies", {}), **package_json.get("devDependencies", {})}

    scan["stack"].append("node")
    package_manager = _detect_package_manager(repo_root)
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

    workspaces = package_json.get("workspaces")
    if workspaces or (repo_root / "pnpm-workspace.yaml").exists():
        scan["framework"].append("monorepo")
    if (repo_root / "turbo.json").exists() or "turbo" in deps:
        scan["framework"].append("turborepo")
    if (repo_root / "nx.json").exists() or "nx" in deps:
        scan["framework"].append("nx")

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
    if "build-system" in pyproject_text:
        scan["commands"].setdefault("build", "python -m build")


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


def _detect_c_family(repo_root: Path, scan: dict) -> None:
    cmake_text = _read_text(repo_root / "CMakeLists.txt")
    file_names = {path.name for path in repo_root.iterdir() if path.is_file()}
    has_c = any(name.endswith((".c", ".h")) for name in file_names)
    has_cpp = any(name.endswith((".cpp", ".cc", ".cxx", ".hpp", ".hh", ".hxx")) for name in file_names)

    if not cmake_text and not has_c and not has_cpp:
        return

    language = None
    if "cxx" in cmake_text or has_cpp:
        language = "cpp"
    elif " project(" in f" {cmake_text}" or has_c:
        language = "c"

    if not language:
        return

    scan["stack"].append(language)
    if cmake_text:
        scan["framework"].append("cmake")
        scan["package_manager"].append("cmake")
        scan["commands"].setdefault("configure", "cmake -S . -B build")
        scan["commands"].setdefault("build", "cmake -S . -B build && cmake --build build")
        scan["commands"].setdefault("test", "ctest --test-dir build")
    else:
        compiler = "g++" if language == "cpp" else "gcc"
        source = "main.cpp" if language == "cpp" else "main.c"
        scan["package_manager"].append(compiler)
        scan["commands"].setdefault("build", f"{compiler} {source} -o app")


def _unique(values: list[str]) -> list[str]:
    seen = set()
    ordered = []
    for value in values:
        if value not in seen:
            seen.add(value)
            ordered.append(value)
    return ordered


def _detect_repo_state(repo_root: Path, scan: dict) -> None:
    tracked_files_raw = _safe_run(repo_root, ["git", "ls-files"])
    tracked_files = [line for line in tracked_files_raw.splitlines() if line.strip()]
    scan["tracked_files_count"] = len(tracked_files)

    recent_files_raw = _safe_run(repo_root, ["git", "status", "--short"])
    preferred_recent_files = []
    low_signal_recent_files = []
    for line in recent_files_raw.splitlines():
        if not line.strip():
            continue
        candidate = _status_candidate(line)
        normalized = _normalize_recent_path(candidate)
        bucket = low_signal_recent_files if _is_low_signal_path(normalized) else preferred_recent_files
        if normalized and normalized not in bucket:
            bucket.append(normalized)
    recent_files = preferred_recent_files or low_signal_recent_files
    scan["recent_files"] = recent_files[:8]

    recent_commits_raw = _safe_run(repo_root, ["git", "log", "--oneline", "-3"])
    scan["recent_commits"] = [line.strip() for line in recent_commits_raw.splitlines() if line.strip()]

    if tracked_files:
        if len(tracked_files) <= 8:
            scan["project_phase"] = "greenfield"
        elif recent_files:
            scan["project_phase"] = "active"
        else:
            scan["project_phase"] = "established"
    else:
        scan["project_phase"] = "greenfield"

    if recent_files:
        scan["resume_hint"] = f"Resume from the latest dirty files first: {', '.join(recent_files[:3])}."
    elif scan["source_dirs"]:
        scan["resume_hint"] = f"Resume from the main source area: {', '.join(scan['source_dirs'][:2])}."
    else:
        scan["resume_hint"] = "Resume from the smallest runnable slice and confirm the test command."


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
        "packages": [],
        "dirs": dirs,
        "tracked_files_count": 0,
        "recent_files": [],
        "recent_commits": [],
        "project_phase": "greenfield",
        "resume_hint": "",
    }

    _detect_node(repo_root, scan)
    _detect_python(repo_root, scan)
    _detect_go(repo_root, scan)
    _detect_rust(repo_root, scan)
    _detect_c_family(repo_root, scan)

    scan["stack"] = _unique(scan["stack"]) or ["generic"]
    scan["framework"] = _unique(scan["framework"]) or ["generic"]
    scan["package_manager"] = _unique(scan["package_manager"]) or ["unknown"]

    scan["important_files"] = _unique([*scan.get("important_files", []), *[name for name in IMPORTANT_FILES if name in files]])
    scan["source_dirs"] = _unique([*scan.get("source_dirs", []), *[name for name in dirs if name in SOURCE_DIR_CANDIDATES]])
    _detect_repo_state(repo_root, scan)
    return scan


def recommend_next_action(scan: dict) -> str:
    if scan.get("recent_files"):
        return f"Review the latest changed files first ({', '.join(scan['recent_files'][:3])}), then continue the smallest unfinished slice."
    if scan.get("project_phase") == "greenfield":
        return "Bootstrap the smallest runnable slice first, then capture the first real task in TASKS.md."
    if "README.md" not in scan.get("important_files", []):
        return "Create or improve the project README so both humans and agents know how to run the project."
    if scan.get("commands", {}).get("test") == "pytest":
        return "Run the Python test command and record any failing modules before changing code."
    if "monorepo" in scan.get("framework", []):
        return "Map the workspace packages first, then choose the smallest affected app or package before changing code."
    if "node" in scan.get("stack", []):
        return "Confirm the package manager and run the main test or lint command before touching code."
    if "go" in scan.get("stack", []):
        return "Run the Go test command first, then map the smallest safe next change."
    if any(lang in scan.get("stack", []) for lang in ["c", "cpp"]):
        return "Confirm the C/C++ build command first, then isolate the smallest compilation target before editing."
    if "rust" in scan.get("stack", []):
        return "Run cargo test first, then change the smallest crate or module needed."
    return "Validate the local run/test commands, then choose the smallest next task from TASKS.md."
