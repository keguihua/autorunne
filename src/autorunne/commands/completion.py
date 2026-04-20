from __future__ import annotations

SHELL_MODES = {
    "bash": "bash_source",
    "zsh": "zsh_source",
    "fish": "fish_source",
}


def run(shell: str) -> dict:
    normalized = shell.lower()
    if normalized not in SHELL_MODES:
        raise RuntimeError(f"Unsupported shell: {shell}")
    mode = SHELL_MODES[normalized]
    script = f"# Add this to your shell profile\neval \"$(_AUTORUNNE_COMPLETE={mode} autorunne)\"\n"
    return {"shell": normalized, "script": script}
