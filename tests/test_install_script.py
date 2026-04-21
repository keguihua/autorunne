from __future__ import annotations

import os
import subprocess
from pathlib import Path


SCRIPT_PATH = Path(__file__).resolve().parents[1] / "scripts" / "install.sh"


def _run_install_script(*, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.update(
        {
            "AUTORUNNE_DRY_RUN": "1",
            "AUTORUNNE_PIPX_BIN": "pipx",
        }
    )
    if extra_env:
        env.update(extra_env)
    return subprocess.run(["bash", str(SCRIPT_PATH)], text=True, capture_output=True, env=env, check=False)


def test_install_script_dry_run_defaults_to_pypi_install_and_prints_vscode_flow():
    result = _run_install_script()
    assert result.returncode == 0
    assert "Installing Autorunne from autorunne" in result.stdout
    assert "autorunne open --with-vscode" in result.stdout
    assert "launch Codex or Claude Code directly from that repo" in result.stdout
    assert "fallback install modes" in result.stdout


def test_install_script_dry_run_can_target_release_wheel():
    result = _run_install_script(
        extra_env={
            "AUTORUNNE_INSTALL_SOURCE": "release-wheel",
            "AUTORUNNE_VERSION": "v0.6.3",
        }
    )
    assert result.returncode == 0
    assert "releases/download/v0.6.3/autorunne-0.6.3-py3-none-any.whl" in result.stdout
    assert "Resolved pipx runner: pipx" in result.stdout
