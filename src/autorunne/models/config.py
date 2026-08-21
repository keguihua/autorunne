from pathlib import Path
from pydantic import BaseModel, Field

from autorunne import __version__ as AUTORUNNE_VERSION


class WorkflowConfig(BaseModel):
    version: str = AUTORUNNE_VERSION
    workflow_dir: str = ".autorunne"
    export_dir: str = ".dist-release"
    excluded_paths: list[str] = Field(
        default_factory=lambda: [
            ".autorunne",
            ".dist-release",
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
        ]
    )
    auto_record_ignored_paths: list[str] = Field(
        default_factory=lambda: [
            ".codex",
            ".agents",
            ".claude",
            ".cursor",
            ".github/copilot-instructions.md",
            "AGENTS.md",
        ]
    )
    preferred_agent: str = "common"
    auto_validate_on_finish: bool = True
    auto_record_on_change: bool = True
    auto_compact_enabled: bool = True
    auto_compact_threshold: int = 1000
    auto_compact_keep_sessions: int = 200

    @property
    def workflow_path(self) -> Path:
        return Path(self.workflow_dir)
