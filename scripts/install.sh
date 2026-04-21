#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/keguihua/autorunne.git"
AUTORUNNE_REF="${AUTORUNNE_GIT_REF:-main}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "autorunne installer requires python3" >&2
  exit 1
fi

PIPX_BIN=""
if command -v pipx >/dev/null 2>&1; then
  PIPX_BIN="$(command -v pipx)"
else
  if python3 -c 'import sys; raise SystemExit(0 if sys.prefix != sys.base_prefix else 1)'; then
    echo "Installing pipx into a local bootstrap venv because you are already inside a virtualenv..."
    BOOTSTRAP_DIR="$HOME/.local/pipx-bootstrap"
    python3 -m venv "$BOOTSTRAP_DIR"
    "$BOOTSTRAP_DIR/bin/pip" install --upgrade pipx
    PIPX_BIN="$BOOTSTRAP_DIR/bin/pipx"
  else
    echo "Installing pipx into your user environment..."
    python3 -m pip install --user --upgrade pipx
    python3 -m pipx ensurepath >/dev/null 2>&1 || true
    if [ -x "$HOME/.local/bin/pipx" ]; then
      PIPX_BIN="$HOME/.local/bin/pipx"
    else
      PIPX_BIN="python3 -m pipx"
    fi
  fi
fi

INSTALL_TARGET="git+$REPO_URL"
if [ "$AUTORUNNE_REF" != "main" ]; then
  INSTALL_TARGET="git+$REPO_URL@$AUTORUNNE_REF"
fi

echo "Installing Autorunne from $INSTALL_TARGET"
if [ "$PIPX_BIN" = "python3 -m pipx" ]; then
  python3 -m pipx install --force "$INSTALL_TARGET"
else
  "$PIPX_BIN" install --force "$INSTALL_TARGET"
fi

echo
echo "Autorunne installed."
echo "Next steps:"
echo "  1) cd /path/to/your/repo"
echo "  2) autorunne open --with-vscode"
echo "  3) after that, just open the repo and let Autorunne auto-resume it"
