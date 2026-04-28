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


def test_chinese_manual_documents_monorepo_support():
    text = MANUAL.read_text(encoding="utf-8")
    assert "多包项目 / Monorepo 支持" in text
    assert "根目录没有 `package.json` 也没关系" in text
    assert "frontend/package.json" in text
    assert "backend/package.json" in text
    assert "contracts/package.json" in text
    assert "apps/*" in text
    assert "packages/*" in text
    assert "cd frontend && npm run build" in text
    assert "sync` 不应该再把项目误判" in text
