"""
Ashiee Skills Tool
Allows the model to discover and load skill runbooks on-demand.
"""

from typing import Any
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.skills.manager import SkillManager


class LoadSkillTool(BaseTool):
    name = "load_skill"
    description = "Load the full procedural instructions and workflows for a specific skill into context."
    parameters = {
        "type": "object",
        "properties": {
            "skill_name": {"type": "string", "description": "The exact name of the skill to load."},
        },
        "required": ["skill_name"],
    }

    def __init__(self, skill_manager: SkillManager):
        self.skill_manager = skill_manager

    async def execute(self, skill_name: str, **kwargs: Any) -> ToolResult:
        content = self.skill_manager.load_skill_content(skill_name)
        if not content:
            available = list(self.skill_manager._skills.keys())
            return ToolResult(
                success=False,
                output=f"Skill '{skill_name}' not found. Available skills: {', '.join(available) if available else 'None'}"
            )
        return ToolResult(
            success=True,
            output=f"--- [Skill: {skill_name}] ---\n{content}\n--- [End of Skill: {skill_name}] ---"
        )


class ListSkillsTool(BaseTool):
    name = "list_skills"
    description = "List all available skills discovered in workspace, global, or builtin directories."
    parameters = {
        "type": "object",
        "properties": {},
    }

    def __init__(self, skill_manager: SkillManager):
        self.skill_manager = skill_manager

    async def execute(self, **kwargs: Any) -> ToolResult:
        summary = self.skill_manager.get_skill_summary_prompt()
        return ToolResult(success=True, output=summary)
