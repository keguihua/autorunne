from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
import json
import os
from pathlib import Path
from typing import Callable
import urllib.request

from autorunne.core.paths import ensure_dir

PYPI_JSON_URL = "https://pypi.org/pypi/autorunne/json"
DEFAULT_TTL_SECONDS = 24 * 60 * 60
SAFE_UPGRADE_COMMAND = "pipx upgrade autorunne --pip-args '--no-cache-dir -i https://pypi.org/simple'"


@dataclass(frozen=True)
class UpdateCheckResult:
    current_version: str
    latest_version: str | None
    has_update: bool
    notice: str | None = None
    from_cache: bool = False
    error: str | None = None


def parse_version(version: str) -> tuple[int, ...]:
    clean = version.strip().removeprefix("v")
    parts: list[int] = []
    for token in clean.split("."):
        digits = ""
        for char in token:
            if char.isdigit():
                digits += char
            else:
                break
        parts.append(int(digits or 0))
    return tuple(parts)


def fetch_latest_version(timeout: float = 2.0) -> str:
    with urllib.request.urlopen(PYPI_JSON_URL, timeout=timeout) as response:
        data = json.load(response)
    return str(data["info"]["version"])


def build_update_notice(current_version: str, latest_version: str) -> str:
    return (
        f"New AutoRunne version available: {latest_version} (installed: {current_version}).\n"
        "AutoRunne is not auto-upgraded by default, so your machine and project state stay under your control.\n"
        "Upgrade with:\n"
        f"  {SAFE_UPGRADE_COMMAND}\n"
        "Or run:\n"
        "  autorunne self-upgrade"
    )


def _read_cache(cache_path: Path, ttl_seconds: int) -> str | None:
    if not cache_path.exists():
        return None
    try:
        payload = json.loads(cache_path.read_text(encoding="utf-8"))
        checked_at = datetime.fromisoformat(payload["checked_at"])
        if checked_at.tzinfo is None:
            checked_at = checked_at.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - checked_at).total_seconds()
        if age <= ttl_seconds:
            return str(payload.get("latest_version") or "") or None
    except Exception:
        return None
    return None


def _write_cache(cache_path: Path, latest_version: str) -> None:
    ensure_dir(cache_path.parent)
    payload = {
        "latest_version": latest_version,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }
    cache_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def check_for_update(
    *,
    current_version: str,
    cache_path: Path | None = None,
    fetch_latest: Callable[[], str] = fetch_latest_version,
    force: bool = False,
    ttl_seconds: int = DEFAULT_TTL_SECONDS,
) -> UpdateCheckResult:
    if os.environ.get("AUTORUNNE_DISABLE_UPDATE_CHECK") == "1":
        return UpdateCheckResult(current_version=current_version, latest_version=None, has_update=False)

    latest: str | None = None
    from_cache = False
    if cache_path is not None and not force:
        latest = _read_cache(cache_path, ttl_seconds)
        from_cache = latest is not None

    if latest is None:
        try:
            latest = fetch_latest()
            if cache_path is not None:
                _write_cache(cache_path, latest)
        except Exception as exc:
            return UpdateCheckResult(current_version=current_version, latest_version=None, has_update=False, error=str(exc))

    has_update = parse_version(latest) > parse_version(current_version)
    notice = build_update_notice(current_version, latest) if has_update else None
    return UpdateCheckResult(
        current_version=current_version,
        latest_version=latest,
        has_update=has_update,
        notice=notice,
        from_cache=from_cache,
    )
