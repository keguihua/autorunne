from pathlib import Path

from autorunne.core.exporter import export_clean_copy
from autorunne.core.gitops import ensure_local_exclude
from autorunne.core.paths import save_config
from autorunne.models.config import WorkflowConfig


def test_ensure_local_exclude_is_idempotent(git_repo: Path):
    first = ensure_local_exclude(git_repo)
    second = ensure_local_exclude(git_repo)
    assert first == second
    lines = [line.strip() for line in first.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert lines.count('.autorunne/') == 1


def test_export_clean_copy_skips_export_root(git_repo: Path):
    save_config(git_repo, WorkflowConfig())
    (git_repo / '.autorunne').mkdir(exist_ok=True)
    (git_repo / '.autorunne' / 'PROJECT_CONTEXT.md').write_text('x\n', encoding='utf-8')
    (git_repo / 'README.md').write_text('hello\n', encoding='utf-8')
    exported = export_clean_copy(git_repo)
    assert exported.exists()
    assert (exported / 'README.md').exists()
    assert not (exported / '.autorunne').exists()
