from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MANUAL = ROOT / "docs" / "Autorunne-操作手册-ZH.md"
USAGE_ZH = ROOT / "docs" / "Autorunne-Usage-ZH.md"
USAGE_EN = ROOT / "docs" / "Autorunne-Usage-EN.md"
PRODUCT_BRIEF = ROOT / "docs" / "Autorunne-产品说明书-ZH.md"
BUSINESS_PLAN = ROOT / "docs" / "Autorunne-商业计划书-ZH.md"
SALES_POSITIONING = ROOT / "docs" / "Autorunne-对外定位与销售话术-ZH.md"
RELEASE_NOTES_0613 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.13-ZH.md"
RELEASE_NOTES_0614 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.14-ZH.md"
RELEASE_NOTES_0615 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.15-ZH.md"
RELEASE_NOTES_0616 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.16-ZH.md"
RELEASE_NOTES_0620 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.20-ZH.md"
RELEASE_NOTES_0621 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.21-ZH.md"
RELEASE_NOTES_0622 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.22-ZH.md"
RELEASE_NOTES_0629 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.29-ZH.md"
RELEASE_NOTES_0630 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.30-ZH.md"
RELEASE_NOTES_0631 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.31-ZH.md"
RELEASE_NOTES_0634 = ROOT / "docs" / "Autorunne-Release-Notes-0.6.34-ZH.md"
COMMERCIAL_STABILITY = ROOT / "docs" / "Autorunne-商业稳定性说明-ZH.md"


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
    assert "autorunne release --version 0.6.22" in text


def test_usage_guides_are_updated_for_0613_monorepos():
    zh = USAGE_ZH.read_text(encoding="utf-8")
    en = USAGE_EN.read_text(encoding="utf-8")
    for text in (zh, en):
        assert "0.6.13" in text
        assert "frontend/package.json" in text
        assert "backend/package.json" in text
        assert "contracts/package.json" in text
        assert "cd frontend && npm run build" in text
        assert "cd backend && npm test" in text
        assert "cd contracts && npm run compile" in text
        assert "autorunne-0.6.22-py3-none-any.whl" in text
        assert "autorunne release --version 0.6.22" in text


def test_business_docs_position_autorunne_as_repo_local_memory_layer():
    product = PRODUCT_BRIEF.read_text(encoding="utf-8")
    business = BUSINESS_PLAN.read_text(encoding="utf-8")
    sales = SALES_POSITIONING.read_text(encoding="utf-8")
    release = RELEASE_NOTES_0622.read_text(encoding="utf-8")
    commercial = COMMERCIAL_STABILITY.read_text(encoding="utf-8")

    assert "当前版本定位：0.6.31" in product
    assert "repo-local 项目记忆" in product
    assert "frontend/backend/contracts" in product
    assert "商业稳定性结论" in product

    assert "免费开源层（0.6.22 已覆盖）" in business
    assert "Hermes 记住用户和跨项目经验，Autorunne 记住这个 repo 的项目状态" in business
    assert "教学 + 交付 + 顾问服务" in business

    assert "AI 项目记忆与开发工作流内核" in sales
    assert "0.6.22 更适合真实项目演示" in sales

    assert "Autorunne 0.6.22 发布说明" in release
    assert "PyPI：`autorunne==0.6.22`" in release
    assert "商业稳定性说明" in commercial
    assert "可商用验证的 Beta 工作流层" in commercial


def test_usage_guides_are_updated_for_0614_lightweight_python():
    zh = USAGE_ZH.read_text(encoding="utf-8")
    en = USAGE_EN.read_text(encoding="utf-8")
    release = RELEASE_NOTES_0614.read_text(encoding="utf-8")
    for text in (zh, en, release):
        assert "0.6.14" in text
        assert "python app.py" in text
        assert "python -m pytest -q" in text
        assert "app.py" in text
        assert "tests/" in text
    assert "自动读取 Autorunne workflow" in zh
    assert "load the Autorunne workflow automatically" in en
    assert "不需要用户每次提醒" in release


def test_release_notes_0616_documents_status_visualization():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = RELEASE_NOTES_0616.read_text(encoding="utf-8")
    assert "0.6.16" in readme
    assert "用户摘要" in release
    assert "STATUS.md" in release
    assert "open/sync → start/ingest → checkpoint → finish/validate" in release
    assert "GitHub Release" in release
    assert "PyPI：`autorunne==0.6.16`" in release
    assert "商业稳定性判断" in release


def test_release_notes_0629_documents_long_term_memory_commands():
    release = RELEASE_NOTES_0629.read_text(encoding="utf-8")
    assert "autorunne compact" in release
    assert "autorunne memory-report" in release
    assert "autorunne export-session" in release
    assert "默认保留 200 条" in release
    assert "PyPI：`autorunne==0.6.29`" in release


def test_release_notes_0630_documents_auto_compaction_defaults():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = RELEASE_NOTES_0630.read_text(encoding="utf-8")
    assert "0.6.30" in readme
    assert "默认超过 1000 条" in release
    assert "保留最近 200 条" in release
    assert "auto_compact_threshold" in release
    assert "auto_compact_enabled" in release
    assert "PyPI：`autorunne==0.6.30`" in release


def test_release_notes_0631_documents_automatic_summary_fallback():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    release = RELEASE_NOTES_0631.read_text(encoding="utf-8")
    assert "0.6.31" in readme
    assert "summary 自动生成" in release
    assert "autorunne checkpoint" in release
    assert "autorunne finish" in release
    assert "不需要问用户" in release
    assert "PyPI：`autorunne==0.6.31`" in release


def test_release_notes_0634_document_formal_reliability_release():
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    release = RELEASE_NOTES_0634.read_text(encoding="utf-8")
    assert "0.6.34" in readme
    assert "0.6.34" in changelog
    assert "0.6.34" in release
    assert "原子" in release
    assert "备份" in release
    assert "同月" in release
    assert "状态：正式发布" in release
    assert "daemon" in release
    assert "worktree" in release
    assert "releases/tag/v0.6.34" in release
    assert "pypi.org/project/autorunne/0.6.34" in release
    assert "当前公开版本：**0.6.34**" in readme
