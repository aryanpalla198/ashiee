"""
Ashiee Subagent Tools
Allows the agent to delegate sub-tasks to child agents in parallel.
"""

from typing import Any
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.core.subagent import SubagentPool


class InvokeSubagentTool(BaseTool):
    name = "invoke_subagent"
    description = "Launch an autonomous child agent for a dedicated task (e.g., Code Researcher, Tester)."
    parameters = {
        "type": "object",
        "properties": {
            "role": {"type": "string", "description": "Role of the subagent (e.g. 'Code Researcher')."},
            "prompt": {"type": "string", "description": "Specific instruction for the subagent."},
        },
        "required": ["role", "prompt"],
    }

    def __init__(self, subagent_pool: SubagentPool):
        self.subagent_pool = subagent_pool

    async def execute(self, role: str, prompt: str, **kwargs: Any) -> ToolResult:
        task = await self.subagent_pool.spawn_subagent(role=role, prompt=prompt)
        return ToolResult(
            success=True,
            output=f"Spawned subagent '{task.id}' with role '{role}'. Status: {task.status}",
            metadata={"task_id": task.id, "role": role}
        )


class ManageSubagentsTool(BaseTool):
    name = "manage_subagents"
    description = "List all active or completed background subagents and inspect their results."
    parameters = {
        "type": "object",
        "properties": {
            "action": {
                "type": "string",
                "enum": ["list", "status"],
                "description": "Action to perform."
            },
            "task_id": {
                "type": "string",
                "description": "Optional task ID to inspect if action is 'status'."
            }
        },
        "required": ["action"],
    }

    def __init__(self, subagent_pool: SubagentPool):
        self.subagent_pool = subagent_pool

    async def execute(self, action: str, task_id: str = None, **kwargs: Any) -> ToolResult:
        if action == "list":
            tasks = self.subagent_pool.list_subagents()
            if not tasks:
                return ToolResult(success=True, output="No subagents have been spawned in this session.")
            lines = [f"- ID: {t.id} | Role: {t.role} | Status: {t.status}" for t in tasks]
            return ToolResult(success=True, output="Active and completed subagents:\n" + "\n".join(lines))
        elif action == "status" and task_id:
            task = self.subagent_pool.get_subagent(task_id)
            if not task:
                return ToolResult(success=False, output=f"Subagent '{task_id}' not found.")
            return ToolResult(
                success=True,
                output=f"Subagent: {task.id}\nRole: {task.role}\nStatus: {task.status}\nResult: {task.result or 'In progress'}"
            )
        return ToolResult(success=False, output="Invalid subagent action or missing task_id.")
