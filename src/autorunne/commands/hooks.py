from __future__ import annotations

from pathlib import Path

from autorunne.core.gitops import detect_repo_root

PRE_COMMIT_YAML = """repos:
  - repo: local
    hooks:
      - id: autorunne-doctor
        name: autorunne doctor
        entry: autorunne doctor
        language: system
        pass_filenames: false
"""


def install_hook(target: Path, hook_name: str, script_body: str) -> Path:
    hook_path = target / ".git" / "hooks" / hook_name
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(script_body, encoding="utf-8")
    hook_path.chmod(0o755)
    return hook_path


def _write_precommit_config(target: Path) -> Path:
    config_path = target / ".pre-commit-config.yaml"
    if not config_path.exists():
        config_path.write_text(PRE_COMMIT_YAML, encoding="utf-8")
    return config_path


def run(target: Path, with_pre_commit: bool = False) -> dict:
    repo_root = detect_repo_root(target) or target
    if not (repo_root / ".git").exists():
        raise RuntimeError("autorunne hooks must run inside an existing git repository")
    sync_script = "#!/usr/bin/env sh\nautorunne sync >/dev/null 2>&1 || true\n"
    post_checkout = install_hook(repo_root, "post-checkout", sync_script)
    post_merge = install_hook(repo_root, "post-merge", sync_script)
    hooks = [str(post_checkout), str(post_merge)]
    precommit_config = None
    if with_pre_commit:
        pre_script = "#!/usr/bin/env sh\nautorunne doctor >/dev/null 2>&1 || exit 1\n"
        pre_commit_hook = install_hook(repo_root, "pre-commit", pre_script)
        hooks.append(str(pre_commit_hook))
        precommit_config = str(_write_precommit_config(repo_root))
    return {"repo_root": str(repo_root), "hooks": hooks, "precommit_config": precommit_config}
