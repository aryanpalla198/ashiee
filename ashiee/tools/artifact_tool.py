"""
Ashiee Artifacts System
Creates structured markdown, reports, and generative UI documents.
"""

from pathlib import Path
from typing import Any, Optional
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.config import AshieeConfig


class CreateArtifactTool(BaseTool):
    name = "create_artifact"
    description = "Create a persistent structured artifact (report, design, diff, or diagram) to present to the user."
    parameters = {
        "type": "object",
        "properties": {
            "title": {"type": "string", "description": "Title or short identifier for the artifact."},
            "filename": {"type": "string", "description": "File name (e.g., 'architecture_report.md')."},
            "content": {"type": "string", "description": "Markdown / Mermaid / HTML content of the artifact."},
            "summary": {"type": "string", "description": "Summary of what this artifact contains."},
        },
        "required": ["title", "filename", "content", "summary"],
    }

    def __init__(self, config: AshieeConfig, artifacts_dir: Optional[Path] = None):
        self.config = config
        self.artifacts_dir = artifacts_dir or (config.app_data_dir / "artifacts")
        self.artifacts_dir.mkdir(parents=True, exist_ok=True)

    async def execute(self, title: str, filename: str, content: str, summary: str, **kwargs: Any) -> ToolResult:
        try:
            target = self.artifacts_dir / filename
            target.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Artifact '{title}' successfully created at: {target}\nSummary: {summary}",
                metadata={"title": title, "path": str(target), "summary": summary}
            )
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to create artifact: {str(e)}")
