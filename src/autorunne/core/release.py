from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

from autorunne.core.exporter import export_clean_copy


def _run(command: list[str], cwd: Path) -> None:
    subprocess.run(command, cwd=cwd, check=True, text=True)


def _git_commit_sha(repo_root: Path) -> str | None:
    result = subprocess.run(["git", "rev-parse", "HEAD"], cwd=repo_root, text=True, capture_output=True)
    if result.returncode != 0:
        return None
    return result.stdout.strip()


def create_release_bundle(repo_root: Path, version: str, build_packages: bool = True) -> dict:
    clean_version = version if version.startswith("v") else f"v{version}"
    releases_root = repo_root / ".dist-release" / "releases"
    release_dir = releases_root / clean_version
    if release_dir.exists():
        shutil.rmtree(release_dir)
    release_dir.mkdir(parents=True, exist_ok=True)

    exported_repo = export_clean_copy(repo_root, output_name="repo")
    target_repo = release_dir / "repo"
    if target_repo.exists():
        shutil.rmtree(target_repo)
    shutil.move(str(exported_repo), str(target_repo))

    notes = f"# Release {clean_version}\n\n- Source repo: {repo_root.name}\n- Clean export path: repo/\n- Autorunne files removed from release export\n"
    notes_path = release_dir / "RELEASE_NOTES.md"
    notes_path.write_text(notes, encoding="utf-8")

    built_assets: list[str] = []
    if build_packages:
        _run(["python", "-m", "build"], cwd=repo_root)
        dist_dir = repo_root / "dist"
        assets_dir = release_dir / "assets"
        assets_dir.mkdir(parents=True, exist_ok=True)
        for artifact in dist_dir.glob("*"):
            destination = assets_dir / artifact.name
            shutil.copy2(artifact, destination)
            built_assets.append(str(destination))

    manifest = {
        "version": clean_version,
        "repo_name": repo_root.name,
        "git_commit": _git_commit_sha(repo_root),
        "release_dir": str(release_dir),
        "exported_repo": str(target_repo),
        "notes_path": str(notes_path),
        "assets": built_assets,
    }
    manifest_path = release_dir / "MANIFEST.json"
    manifest_path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

    return {**manifest, "manifest_path": str(manifest_path)}
