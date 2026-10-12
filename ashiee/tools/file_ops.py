"""
Ashiee File Operations Tools
Implements view_file, write_to_file, and replace_file_content with boundary security.
"""

from pathlib import Path
from typing import Any, Optional
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.config import AshieeConfig, FileAccessPolicy


class FileToolHelper:
    @staticmethod
    def resolve_and_verify_path(rel_or_abs_path: str, config: AshieeConfig) -> Path:
        resolved = Path(rel_or_abs_path)
        if not resolved.is_absolute():
            resolved = (config.workspace_root / resolved).resolve()
        else:
            resolved = resolved.resolve()

        # Check boundary
        try:
            resolved.relative_to(config.workspace_root.resolve())
        except ValueError:
            if config.security.file_access_policy == FileAccessPolicy.DENY:
                raise PermissionError(
                    f"Access denied: Path '{resolved}' is outside the workspace root '{config.workspace_root}'."
                )
        return resolved


class ViewFileTool(BaseTool):
    name = "view_file"
    description = "View the contents of a file with line numbering and optional line-range slicing."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path to the file to inspect."},
            "start_line": {"type": "integer", "description": "Optional 1-indexed start line."},
            "end_line": {"type": "integer", "description": "Optional 1-indexed end line."},
        },
        "required": ["path"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(self, path: str, start_line: Optional[int] = None, end_line: Optional[int] = None, **kwargs: Any) -> ToolResult:
        try:
            target = FileToolHelper.resolve_and_verify_path(path, self.config)
            if not target.exists():
                return ToolResult(success=False, output=f"File not found: {path}")
            if target.is_dir():
                return ToolResult(success=False, output=f"Path is a directory, not a file: {path}")

            lines = target.read_text(encoding="utf-8", errors="replace").splitlines()
            total_lines = len(lines)

            start = max(1, start_line or 1)
            end = min(total_lines, end_line or total_lines)

            if start > total_lines:
                return ToolResult(
                    success=True,
                    output=f"[File has only {total_lines} lines; requested start line is {start}]"
                )

            formatted = []
            for idx in range(start - 1, end):
                formatted.append(f"{idx + 1}: {lines[idx]}")

            header = f"File: {path} ({total_lines} total lines, showing lines {start} to {end}):\n"
            return ToolResult(success=True, output=header + "\n".join(formatted))
        except Exception as e:
            return ToolResult(success=False, output=str(e))


class WriteToFileTool(BaseTool):
    name = "write_to_file"
    description = "Create a new file or overwrite an existing file with complete content."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to create or write to."},
            "content": {"type": "string", "description": "Full text content to write."},
            "overwrite": {"type": "boolean", "description": "Whether to overwrite if file already exists."},
        },
        "required": ["path", "content"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(self, path: str, content: str, overwrite: bool = True, **kwargs: Any) -> ToolResult:
        try:
            target = FileToolHelper.resolve_and_verify_path(path, self.config)
            if target.exists() and not overwrite:
                return ToolResult(
                    success=False,
                    output=f"File '{path}' already exists and overwrite is set to False."
                )

            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
            return ToolResult(
                success=True,
                output=f"Successfully wrote {len(content)} characters to '{path}'."
            )
        except Exception as e:
            return ToolResult(success=False, output=str(e))


class ReplaceFileContentTool(BaseTool):
    name = "replace_file_content"
    description = "Replace a specific contiguous block of text in an existing file with replacement text."
    parameters = {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path of the file to modify."},
            "target_content": {"type": "string", "description": "Exact text block to replace."},
            "replacement_content": {"type": "string", "description": "New replacement text."},
            "allow_multiple": {"type": "boolean", "description": "Allow replacing multiple occurrences."},
        },
        "required": ["path", "target_content", "replacement_content"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(
        self,
        path: str,
        target_content: str,
        replacement_content: str,
        allow_multiple: bool = False,
        **kwargs: Any
    ) -> ToolResult:
        try:
            target = FileToolHelper.resolve_and_verify_path(path, self.config)
            if not target.exists():
                return ToolResult(success=False, output=f"File not found: {path}")

            original = target.read_text(encoding="utf-8")
            count = original.count(target_content)

            if count == 0:
                return ToolResult(
                    success=False,
                    output=f"Target content not found in '{path}'. Please inspect the file again to verify exact match."
                )

            if count > 1 and not allow_multiple:
                return ToolResult(
                    success=False,
                    output=f"Found {count} occurrences of target content in '{path}'. Set allow_multiple=True or provide more context lines to ensure uniqueness."
                )

            updated = original.replace(target_content, replacement_content, -1 if allow_multiple else 1)
            target.write_text(updated, encoding="utf-8")

            # Generate unified diff for Antigravity-style Visual Diff Card
            import difflib
            diff_lines = list(difflib.unified_diff(
                original.splitlines(keepends=True),
                updated.splitlines(keepends=True),
                fromfile=f"a/{path}",
                tofile=f"b/{path}",
                n=3
            ))
            diff_str = "".join(diff_lines)

            return ToolResult(
                success=True,
                output=f"Successfully replaced {count if allow_multiple else 1} occurrence(s) in '{path}'.\n\n```diff\n{diff_str}\n```" if diff_str else f"Successfully replaced {count if allow_multiple else 1} occurrence(s) in '{path}'.",
                metadata={"diff": diff_str, "path": path}
            )
        except Exception as e:
            return ToolResult(success=False, output=str(e))
