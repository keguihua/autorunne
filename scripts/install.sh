#!/usr/bin/env bash
set -euo pipefail

REPO_URL="https://github.com/keguihua/autorunne.git"
RELEASE_BASE_URL="https://github.com/keguihua/autorunne/releases/download"
AUTORUNNE_REF="${AUTORUNNE_GIT_REF:-main}"
AUTORUNNE_INSTALL_SOURCE="${AUTORUNNE_INSTALL_SOURCE:-pypi}"
AUTORUNNE_VERSION="${AUTORUNNE_VERSION:-}"
AUTORUNNE_DRY_RUN="${AUTORUNNE_DRY_RUN:-0}"
AUTORUNNE_PIPX_BIN_OVERRIDE="${AUTORUNNE_PIPX_BIN:-}"
AUTORUNNE_PIP_ARGS="${AUTORUNNE_PIP_ARGS:---no-cache-dir -i https://pypi.org/simple}"

if ! command -v python3 >/dev/null 2>&1; then
  echo "autorunne installer requires python3" >&2
  exit 1
fi

PIPX_BIN=""
if [ -n "$AUTORUNNE_PIPX_BIN_OVERRIDE" ]; then
  PIPX_BIN="$AUTORUNNE_PIPX_BIN_OVERRIDE"
elif command -v pipx >/dev/null 2>&1; then
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

resolve_install_target() {
  case "$AUTORUNNE_INSTALL_SOURCE" in
    git)
      INSTALL_TARGET="git+$REPO_URL"
      if [ "$AUTORUNNE_REF" != "main" ]; then
        INSTALL_TARGET="git+$REPO_URL@$AUTORUNNE_REF"
      fi
      ;;
    release-wheel)
      VERSION_TAG="$AUTORUNNE_VERSION"
      if [ -z "$VERSION_TAG" ]; then
        VERSION_TAG="$AUTORUNNE_REF"
      fi
      if [ -z "$VERSION_TAG" ] || [ "$VERSION_TAG" = "main" ]; then
        echo "AUTORUNNE_VERSION (for example v0.6.1) is required when AUTORUNNE_INSTALL_SOURCE=release-wheel" >&2
        exit 1
      fi
      VERSION_BASE="${VERSION_TAG#v}"
      INSTALL_TARGET="$RELEASE_BASE_URL/$VERSION_TAG/autorunne-$VERSION_BASE-py3-none-any.whl"
      ;;
    pypi)
      INSTALL_TARGET="autorunne"
      ;;
    *)
      echo "Unsupported AUTORUNNE_INSTALL_SOURCE: $AUTORUNNE_INSTALL_SOURCE" >&2
      exit 1
      ;;
  esac
}

resolve_install_target

echo "Installing Autorunne from $INSTALL_TARGET"
echo "Resolved pipx runner: $PIPX_BIN"
if [ "$AUTORUNNE_INSTALL_SOURCE" = "pypi" ]; then
  echo "Pip args: $AUTORUNNE_PIP_ARGS"
fi
if [ "$AUTORUNNE_DRY_RUN" = "1" ]; then
  echo
  echo "Dry run only. No changes were made."
elif [ "$PIPX_BIN" = "python3 -m pipx" ]; then
  if [ "$AUTORUNNE_INSTALL_SOURCE" = "pypi" ]; then
    python3 -m pipx install --force "$INSTALL_TARGET" --pip-args "$AUTORUNNE_PIP_ARGS"
  else
    python3 -m pipx install --force "$INSTALL_TARGET"
  fi
else
  if [ "$AUTORUNNE_INSTALL_SOURCE" = "pypi" ]; then
    "$PIPX_BIN" install --force "$INSTALL_TARGET" --pip-args "$AUTORUNNE_PIP_ARGS"
  else
    "$PIPX_BIN" install --force "$INSTALL_TARGET"
  fi
fi

echo
echo "Autorunne installed."
echo "Next steps:"
echo "  1) cd /path/to/your/repo"
echo "  2) first time in that repo, run: autorunne open --with-vscode"
echo "  3) after that, just open the repo in VS Code and let Autorunne auto-resume it"
echo "  4) then launch Codex or Claude Code directly from that repo terminal — you do not need a separate Autorunne window unless you explicitly want daemon mode"
echo "  5) fallback install modes: AUTORUNNE_INSTALL_SOURCE=git or AUTORUNNE_INSTALL_SOURCE=release-wheel"
