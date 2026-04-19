from __future__ import annotations

from pathlib import Path


def install_hook(target: Path, hook_name: str, script_body: str) -> Path:
    hook_path = target / ".git" / "hooks" / hook_name
    hook_path.parent.mkdir(parents=True, exist_ok=True)
    hook_path.write_text(script_body, encoding="utf-8")
    hook_path.chmod(0o755)
    return hook_path


def run(target: Path) -> dict:
    script = "#!/usr/bin/env sh\nawf sync >/dev/null 2>&1 || true\n"
    post_checkout = install_hook(target, "post-checkout", script)
    post_merge = install_hook(target, "post-merge", script)
    return {"hooks": [str(post_checkout), str(post_merge)]}
