"""
Ashiee Workspace Search Tools
Fast pattern searching (grep) and glob file discovery across the codebase.
"""

import os
import re
from pathlib import Path
from typing import Any, List, Optional
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.config import AshieeConfig

IGNORE_DIRS = {".git", ".svn", "__pycache__", "node_modules", ".venv", "venv", ".idea", ".vscode", "dist", "build"}


class SearchCodeTool(BaseTool):
    name = "search_code"
    description = "Search for a regex or text query across workspace files."
    parameters = {
        "type": "object",
        "properties": {
            "query": {"type": "string", "description": "The search pattern (text or regex)."},
            "file_pattern": {"type": "string", "description": "Optional file glob filter (e.g. '*.py')."},
            "max_results": {"type": "integer", "description": "Maximum number of matched lines to return."},
        },
        "required": ["query"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(
        self,
        query: str,
        file_pattern: Optional[str] = None,
        max_results: int = 50,
        **kwargs: Any
    ) -> ToolResult:
        try:
            pattern = re.compile(query, re.IGNORECASE)
            results = []
            root = self.config.workspace_root

            for dirpath, dirnames, filenames in os.walk(root):
                # Filter out ignored directories in-place
                dirnames[:] = [d for d in dirnames if d not in IGNORE_DIRS and not d.startswith(".")]

                for fname in filenames:
                    if file_pattern and not Path(fname).match(file_pattern):
                        continue

                    file_path = Path(dirpath) / fname
                    rel_path = file_path.relative_to(root)

                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        for line_num, line in enumerate(content.splitlines(), start=1):
                            if pattern.search(line):
                                results.append(f"{rel_path}:{line_num}: {line.strip()}")
                                if len(results) >= max_results:
                                    break
                    except Exception:
                        continue

                    if len(results) >= max_results:
                        break
                if len(results) >= max_results:
                    break

            if not results:
                return ToolResult(success=True, output=f"No matches found for '{query}'.")

            summary = f"Found {len(results)} match(es) for '{query}':\n" + "\n".join(results)
            return ToolResult(success=True, output=summary)
        except Exception as e:
            return ToolResult(success=False, output=str(e))


class FindFilesTool(BaseTool):
    name = "find_files"
    description = "Locate files in the workspace matching a glob pattern (e.g., '**/*.py' or 'src/**/*.ts')."
    parameters = {
        "type": "object",
        "properties": {
            "glob_pattern": {"type": "string", "description": "Glob pattern to match file names or paths."},
            "max_files": {"type": "integer", "description": "Maximum number of files to return."},
        },
        "required": ["glob_pattern"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(self, glob_pattern: str, max_files: int = 100, **kwargs: Any) -> ToolResult:
        try:
            root = self.config.workspace_root
            matched: List[str] = []

            for path in root.glob(glob_pattern):
                # Ignore blacklisted directories
                parts = path.parts
                if any(p in IGNORE_DIRS for p in parts):
                    continue

                rel = path.relative_to(root)
                matched.append(str(rel))
                if len(matched) >= max_files:
                    break

            if not matched:
                return ToolResult(success=True, output=f"No files matched glob '{glob_pattern}'.")

            summary = f"Found {len(matched)} file(s) matching '{glob_pattern}':\n" + "\n".join(matched)
            return ToolResult(success=True, output=summary)
        except Exception as e:
            return ToolResult(success=False, output=str(e))
