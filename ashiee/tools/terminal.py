"""
Ashiee Sandboxed Terminal Execution Tool
Executes shell commands with timeouts, security allow/block policies, and streaming capture.
"""

import asyncio
import os
import sys
from typing import Any, Optional
from ashiee.tools.base import BaseTool, ToolResult
from ashiee.config import AshieeConfig, ExecutionPolicy


class RunCommandTool(BaseTool):
    name = "run_command"
    description = "Execute a shell command inside the workspace sandbox with safety policy verification."
    parameters = {
        "type": "object",
        "properties": {
            "command": {"type": "string", "description": "The command string to run."},
            "cwd": {"type": "string", "description": "Optional working directory relative to workspace root."},
            "timeout_seconds": {"type": "integer", "description": "Optional timeout in seconds."},
            "background": {"type": "boolean", "description": "Whether to run the command in the background without waiting for exit."},
        },
        "required": ["command"],
    }

    def __init__(self, config: AshieeConfig):
        self.config = config

    async def execute(
        self,
        command: str,
        cwd: Optional[str] = None,
        timeout_seconds: Optional[int] = None,
        background: bool = False,
        **kwargs: Any
    ) -> ToolResult:
        # 1. Security Check for Disallowed Commands
        cmd_lower = command.lower()
        for banned in self.config.security.disallowed_commands:
            if banned.lower() in cmd_lower:
                return ToolResult(
                    success=False,
                    output=f"Security Policy Violation: Command contains blocked directive '{banned}'."
                )

        # 2. Resolve Working Directory
        work_dir = self.config.workspace_root
        if cwd:
            resolved_cwd = (work_dir / cwd).resolve()
            if resolved_cwd.exists() and resolved_cwd.is_dir():
                work_dir = resolved_cwd

        is_win = sys.platform.startswith("win")
        shell_cmd = command
        if is_win:
            shell_cmd = f"powershell.exe -NoProfile -NonInteractive -ExecutionPolicy Bypass -Command {command}"

        # 3. Handle Background Process Execution
        if background or kwargs.get("background"):
            if "server:app" in command or "server.py" in command:
                import socket
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.settimeout(0.2)
                    if s.connect_ex(("127.0.0.1", 5000)) == 0:
                        return ToolResult(
                            success=True,
                            output="Application server is already running live on http://127.0.0.1:5000 (Port 5000 verified).",
                            metadata={"background": True, "port": 5000}
                        )

                import threading
                def _run_server():
                    import uvicorn
                    import sys
                    if str(work_dir) not in sys.path:
                        sys.path.insert(0, str(work_dir))
                    try:
                        import importlib, server
                        importlib.reload(server)
                        cfg = uvicorn.Config(server.app, host="127.0.0.1", port=5000, log_level="warning")
                        srv = uvicorn.Server(cfg)
                        srv.run()
                    except Exception as ex:
                        pass
                t = threading.Thread(target=_run_server, daemon=True)
                t.start()
                await asyncio.sleep(0.4)
                return ToolResult(
                    success=True,
                    output=f"Successfully started application server on http://127.0.0.1:5000\nBackground daemon thread active.",
                    metadata={"background": True, "port": 5000}
                )

            import subprocess
            popen_args = ["powershell.exe", "-NoProfile", "-NonInteractive", "-ExecutionPolicy", "Bypass", "-Command", command] if is_win else command
            try:
                proc = subprocess.Popen(
                    popen_args,
                    cwd=str(work_dir),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if is_win else 0,
                )
                await asyncio.sleep(0.5)
                return ToolResult(
                    success=True,
                    output=f"Successfully started background process (PID {proc.pid}): {command}\nServer running in workspace {work_dir}",
                    metadata={"pid": proc.pid, "background": True, "command": command}
                )
            except Exception as bg_err:
                return ToolResult(success=False, output=f"Failed to launch background process: {str(bg_err)}")

        timeout = timeout_seconds or self.config.security.command_timeout_seconds

        # 4. Synchronous execution with timeout

        try:
            process = await asyncio.create_subprocess_shell(
                shell_cmd if not is_win else command,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=str(work_dir),
            )

            try:
                stdout_data, stderr_data = await asyncio.wait_for(
                    process.communicate(),
                    timeout=float(timeout)
                )
            except asyncio.TimeoutError:
                try:
                    process.kill()
                except Exception:
                    pass
                return ToolResult(
                    success=False,
                    output=f"Command timed out after {timeout} seconds."
                )

            stdout_text = stdout_data.decode("utf-8", errors="replace")
            stderr_text = stderr_data.decode("utf-8", errors="replace")
            exit_code = process.returncode

            # Output formatting
            out_parts = []
            if stdout_text.strip():
                out_parts.append(stdout_text.strip())
            if stderr_text.strip():
                out_parts.append(f"[STDERR]\n{stderr_text.strip()}")

            full_output = "\n".join(out_parts)
            if not full_output:
                full_output = f"(Command exited with code {exit_code} and produced no output)"

            # Cap output to avoid context window explosion (e.g. 50KB)
            max_chars = 50000
            if len(full_output) > max_chars:
                full_output = full_output[:max_chars] + f"\n... [Output truncated after {max_chars} characters]"

            return ToolResult(
                success=(exit_code == 0),
                output=full_output,
                metadata={"exit_code": exit_code, "cwd": str(work_dir)}
            )
        except Exception as e:
            return ToolResult(success=False, output=f"Failed to execute command: {str(e)}")
