"""
Ashiee Base Tool Architecture
Provides base class for tools, argument schema generation, and tool registration.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, Optional
import inspect
from pydantic import BaseModel


class ToolResult(BaseModel):
    success: bool
    output: str
    metadata: Dict[str, Any] = {}

    def to_message(self) -> str:
        if self.success:
            return self.output
        return f"Error executing tool: {self.output}"


class BaseTool(ABC):
    name: str
    description: str
    parameters: Dict[str, Any]

    @abstractmethod
    async def execute(self, **kwargs: Any) -> ToolResult:
        """Execute the tool with the given arguments."""
        pass

    def to_function_declaration(self) -> Dict[str, Any]:
        """Returns standard Function Declaration compatible with OpenAI / Gemini."""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    def __init__(self):
        self._tools: Dict[str, BaseTool] = {}

    def register(self, tool: BaseTool) -> None:
        self._tools[tool.name] = tool

    def get(self, name: str) -> Optional[BaseTool]:
        return self._tools.get(name)

    def list_tools(self) -> list[BaseTool]:
        return list(self._tools.values())

    def get_declarations(self) -> list[Dict[str, Any]]:
        return [tool.to_function_declaration() for tool in self._tools.values()]

    async def execute_tool(self, name: str, args: Dict[str, Any]) -> ToolResult:
        tool = self.get(name)
        if not tool:
            return ToolResult(
                success=False,
                output=f"Tool '{name}' is not recognized in the Ashiee registry."
            )
        try:
            return await tool.execute(**args)
        except Exception as e:
            return ToolResult(
                success=False,
                output=f"Exception raised in '{name}': {str(e)}"
            )
