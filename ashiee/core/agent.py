"""
Ashiee Core Agent Engine
Implements the autonomous ReAct reasoning loop, tool execution, and session management.
"""

import asyncio
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
import uuid

from ashiee.config import AshieeConfig
from ashiee.core.context import ContextAssembler
from ashiee.core.llm import BaseLLMProvider, LLMResponse, ToolCallRequest, get_llm_provider
from ashiee.core.subagent import SubagentPool
from ashiee.core.transcript import TranscriptLogger
from ashiee.skills.manager import SkillManager
from ashiee.tools.artifact_tool import CreateArtifactTool
from ashiee.tools.base import BaseTool, ToolRegistry, ToolResult
from ashiee.tools.file_ops import ReplaceFileContentTool, ViewFileTool, WriteToFileTool
from ashiee.tools.search import FindFilesTool, SearchCodeTool
from ashiee.tools.skills_tool import ListSkillsTool, LoadSkillTool
from ashiee.tools.subagent_tool import InvokeSubagentTool, ManageSubagentsTool
from ashiee.tools.terminal import RunCommandTool


class AgentEvent:
    START = "agent_start"
    THOUGHT = "thought"
    TOOL_START = "tool_start"
    TOOL_END = "tool_end"
    CHUNK = "chunk"
    FINISH = "agent_finish"
    ERROR = "agent_error"


EventListener = Callable[[str, Dict[str, Any]], None]


class AshieeAgent:
    def __init__(
        self,
        config: Optional[AshieeConfig] = None,
        session_id: Optional[str] = None,
    ):
        self.config = config or AshieeConfig()
        self.config.ensure_directories()
        self.session_id = session_id or str(uuid.uuid4())

        self.session_dir = self.config.app_data_dir / "sessions" / self.session_id
        self.transcript = TranscriptLogger(self.session_dir)

        # 1. Initialize Subsystems
        self.skill_manager = SkillManager(self.config)
        self.skill_manager.discover_all()

        self.subagent_pool = SubagentPool(self.config)
        self.context_assembler = ContextAssembler(self.config, self.skill_manager)
        self.llm_provider: BaseLLMProvider = get_llm_provider(self.config.llm)

        # 2. Register Built-in Tools
        self.tools = ToolRegistry()
        self._register_default_tools()

        # 3. State & History
        self.messages: List[Dict[str, Any]] = []
        self._event_listeners: List[EventListener] = []

        self._initialize_system_context()

    def add_event_listener(self, listener: EventListener) -> None:
        self._event_listeners.append(listener)

    def _emit(self, event_type: str, data: Dict[str, Any]) -> None:
        for listener in self._event_listeners:
            try:
                listener(event_type, data)
            except Exception:
                pass

    def _register_default_tools(self) -> None:
        self.tools.register(ViewFileTool(self.config))
        self.tools.register(WriteToFileTool(self.config))
        self.tools.register(ReplaceFileContentTool(self.config))
        self.tools.register(RunCommandTool(self.config))
        self.tools.register(SearchCodeTool(self.config))
        self.tools.register(FindFilesTool(self.config))
        self.tools.register(LoadSkillTool(self.skill_manager))
        self.tools.register(ListSkillsTool(self.skill_manager))
        self.tools.register(CreateArtifactTool(self.config, self.session_dir / "artifacts"))
        self.tools.register(InvokeSubagentTool(self.subagent_pool))
        self.tools.register(ManageSubagentsTool(self.subagent_pool))

    def _initialize_system_context(self) -> None:
        system_prompt = self.context_assembler.assemble_system_instructions()
        self.messages.append({"role": "system", "content": system_prompt})
        self.transcript.record_step(role="system", content=system_prompt)

    async def execute_turn(self, user_prompt: str, max_steps: int = 15) -> str:
        """Executes a complete autonomous turn including ReAct reasoning and tool execution."""
        self._emit(AgentEvent.START, {"prompt": user_prompt, "session_id": self.session_id})

        # Add user message
        self.messages.append({"role": "user", "content": user_prompt})
        self.transcript.record_step(role="user", content=user_prompt)

        tool_declarations = self.tools.get_declarations()
        step = 0
        final_response_text = ""

        while step < max_steps:
            step += 1

            # 1. Query LLM
            try:
                llm_response: LLMResponse = await self.llm_provider.generate_response(
                    messages=self.messages,
                    tools_declarations=tool_declarations,
                )
            except Exception as e:
                err_msg = f"LLM Inference failed: {str(e)}"
                self._emit(AgentEvent.ERROR, {"error": err_msg})
                return err_msg

            # 2. Handle Thought / Reasoning & Text Streaming
            if llm_response.thought:
                self._emit(AgentEvent.THOUGHT, {"thought": llm_response.thought})

            if llm_response.text:
                full_text = llm_response.text
                chunk_size = 80
                if len(full_text) > chunk_size:
                    for i in range(0, len(full_text), chunk_size):
                        sub = full_text[i:i + chunk_size]
                        self._emit(AgentEvent.CHUNK, {"delta": sub, "text": full_text[:i + len(sub)]})
                        await asyncio.sleep(0.005)
                else:
                    self._emit(AgentEvent.CHUNK, {"delta": full_text, "text": full_text})

            # 3. Check for Tool Invocations
            if llm_response.tool_calls:
                # Add assistant intent with tool calls
                self.messages.append({
                    "role": "assistant",
                    "content": llm_response.text or None,
                    "tool_calls": [
                        {
                            "id": tc.id,
                            "name": tc.name,
                            "arguments": tc.arguments,
                        }
                        for tc in llm_response.tool_calls
                    ]
                })

                tool_results_for_log = []

                # Execute all requested tools
                for tc in llm_response.tool_calls:
                    self._emit(AgentEvent.TOOL_START, {
                        "call_id": tc.id,
                        "name": tc.name,
                        "arguments": tc.arguments,
                    })

                    # Execute in sandbox
                    result: ToolResult = await self.tools.execute_tool(tc.name, tc.arguments)

                    self._emit(AgentEvent.TOOL_END, {
                        "call_id": tc.id,
                        "name": tc.name,
                        "success": result.success,
                        "output": result.output,
                    })

                    # Append tool result to context
                    self.messages.append({
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": tc.name,
                        "content": result.to_message(),
                    })

                    tool_results_for_log.append({
                        "name": tc.name,
                        "success": result.success,
                        "output": result.output,
                    })

                self.transcript.record_step(
                    role="assistant",
                    content=llm_response.text,
                    thought=llm_response.thought,
                    tool_calls=[tc.model_dump() for tc in llm_response.tool_calls],
                    tool_results=tool_results_for_log,
                )

                # Loop continues so LLM can inspect the observation
                continue
            else:
                # No more tools needed; process output
                final_response_text = llm_response.text
                self.messages.append({"role": "assistant", "content": final_response_text})
                self.transcript.record_step(
                    role="assistant",
                    content=final_response_text,
                    thought=llm_response.thought,
                )
                self._emit(AgentEvent.FINISH, {"response": final_response_text})
                break

        return final_response_text
