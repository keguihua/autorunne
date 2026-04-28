from pathlib import Path
from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    version: str = "0.6.15"
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

    @property
    def workflow_path(self) -> Path:
        return Path(self.workflow_dir)
