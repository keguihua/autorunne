from pathlib import Path
from pydantic import BaseModel, Field


class WorkflowConfig(BaseModel):
    version: str = "0.3.0"
    workflow_dir: str = ".ai-workflow"
    export_dir: str = ".dist-release"
    excluded_paths: list[str] = Field(
        default_factory=lambda: [
            ".ai-workflow",
            ".dist-release",
            ".git",
            ".venv",
            "__pycache__",
            ".pytest_cache",
            "dist",
            "build",
        ]
    )
    preferred_agent: str = "common"

    @property
    def workflow_path(self) -> Path:
        return Path(self.workflow_dir)
