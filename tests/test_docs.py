from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "docs" / "Autorunne-操作手册-ZH.md"


def test_chinese_manual_documents_safe_upgrade_path_and_version_check():
    text = MANUAL.read_text(encoding="utf-8")
    assert "升级 AutoRunne" in text
    assert 'pipx upgrade autorunne --pip-args="--no-cache-dir -i https://pypi.org/simple"' in text
    assert "pipx runpip autorunne show autorunne" in text
    assert "autorunne version" in text
    assert "autorunne --version" in text
    assert "uninstall" in text
    assert "最后 fallback" in text
