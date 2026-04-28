from pathlib import Path

from autorunne import __version__
from autorunne.core.update import build_update_notice, check_for_update, parse_version


def test_parse_version_compares_patch_versions():
    assert parse_version("0.6.12") > parse_version("0.6.9")
    assert parse_version("v0.6.12") == parse_version("0.6.12")


def test_build_update_notice_defaults_to_reminder_not_auto_upgrade():
    notice = build_update_notice(current_version="0.6.11", latest_version="0.6.12")
    assert "New AutoRunne version available: 0.6.12" in notice
    assert "autorunne self-upgrade" in notice
    assert "pipx upgrade autorunne --pip-args '--no-cache-dir -i https://pypi.org/simple'" in notice
    assert "not auto-upgraded" in notice


def test_check_for_update_uses_cache_without_touching_project_state(tmp_path: Path):
    project_file = tmp_path / ".autorunne" / "state" / "current.json"
    project_file.parent.mkdir(parents=True)
    project_file.write_text('{"keep": true}\n', encoding="utf-8")
    cache_path = tmp_path / ".autorunne" / "runtime" / "update_check.json"

    first = check_for_update(
        current_version="0.6.11",
        cache_path=cache_path,
        fetch_latest=lambda: "0.6.12",
        force=True,
    )
    second = check_for_update(
        current_version="0.6.11",
        cache_path=cache_path,
        fetch_latest=lambda: "0.6.13",
        force=False,
        ttl_seconds=86400,
    )

    assert first.latest_version == "0.6.12"
    assert second.latest_version == "0.6.12"
    assert second.from_cache is True
    assert project_file.read_text(encoding="utf-8") == '{"keep": true}\n'


def test_check_for_update_reports_up_to_date(tmp_path: Path):
    result = check_for_update(
        current_version=__version__,
        cache_path=tmp_path / "update.json",
        fetch_latest=lambda: __version__,
        force=True,
    )
    assert result.has_update is False
    assert result.notice is None
