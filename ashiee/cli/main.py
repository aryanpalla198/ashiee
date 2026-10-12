"""
Ashiee Premium Classic CLI
Interactive REPL pair programmer with rich terminal formatting, live spinners, and slash commands.
"""

import asyncio
import os
import sys
from pathlib import Path
import click
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.syntax import Syntax
from rich.text import Text

from ashiee.config import AshieeConfig, ModelProvider, ExecutionPolicy
from ashiee.core.agent import AshieeAgent, AgentEvent

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass

console = Console(safe_box=True)

BANNER = r"""
[bold cyan]    ___         __     _          [/bold cyan]
[bold cyan]   /   |  _____/ /_   (_)__  ___  [/bold cyan]
[bold cyan]  / /| | / ___/ __ \ / / _ \/ _ \ [/bold cyan]
[bold cyan] / ___ |(__  ) / / // /  __/  __/ [/bold cyan]
[bold cyan]/_/  |_/____/_/ /_//_/\___/\___/  [/bold cyan]
[dim italic]Autonomous AI-First Pair Programmer & Agentic Runtime[/dim italic]
"""


def render_banner(config: AshieeConfig, session_id: str):
    console.print(BANNER)
    table = Table.grid(padding=(0, 2))
    table.add_column(style="bold yellow")
    table.add_column(style="white")
    table.add_row("Workspace Root:", str(config.workspace_root))
    table.add_row("Active Provider:", f"{config.llm.provider.value} ({config.llm.model_name})")
    table.add_row("Execution Policy:", config.security.execution_policy.value)
    table.add_row("Session ID:", session_id[:8] + "...")
    console.print(Panel(table, border_style="cyan", title="[bold white]Ashiee Runtime v1.0.0[/bold white]"))
    console.print("[dim]Type your request or use slash commands like [bold]/help[/bold], [bold]/skills[/bold], [bold]/plan[/bold], or [bold]/exit[/bold].[/dim]\n")


def setup_agent_listeners(agent: AshieeAgent):
    def on_event(event_type: str, data: dict):
        if event_type == AgentEvent.THOUGHT:
            thought_text = data.get("thought", "")
            if thought_text.strip():
                console.print(Panel(Text(thought_text, style="dim italic"), title="[magenta]Ashiee Thinking[/magenta]", border_style="magenta", expand=False))
        elif event_type == AgentEvent.TOOL_START:
            name = data.get("name", "unknown")
            args = data.get("arguments", {})
            args_summary = ", ".join(f"{k}='{v}'" if isinstance(v, str) and len(str(v)) < 30 else f"{k}={v}" for k, v in args.items())
            console.print(f"[bold yellow][Tool][/bold yellow] [bold white]{name}[/bold white] [dim]({args_summary})[/dim]")
        elif event_type == AgentEvent.TOOL_END:
            success = data.get("success", False)
            name = data.get("name", "")
            out = data.get("output", "")
            status_style = "[bold green][OK][/bold green]" if success else "[bold red][FAIL][/bold red]"
            preview = out.strip().split("\n")[0][:120] if out.strip() else "(empty)"
            console.print(f"  {status_style} [dim]{name} finished:[/dim] [italic]{preview}[/italic]\n")
        elif event_type == AgentEvent.ERROR:
            console.print(f"[bold red]Error:[/bold red] {data.get('error')}")

    agent.add_event_listener(on_event)


async def run_repl(config: AshieeConfig):
    agent = AshieeAgent(config)
    setup_agent_listeners(agent)
    render_banner(config, agent.session_id)

    from prompt_toolkit import PromptSession
    from prompt_toolkit.styles import Style

    prompt_style = Style.from_dict({
        "prompt": "#00d7ff bold",
    })
    session = PromptSession(style=prompt_style)

    while True:
        try:
            user_input = await session.prompt_async([("class:prompt", "Ashiee ❯ ")])
            user_input = user_input.strip()

            if not user_input:
                continue

            # Handle Slash Commands
            if user_input.startswith("/"):
                cmd = user_input.split()[0].lower()
                if cmd in ["/exit", "/quit", "/q"]:
                    console.print("[yellow]Farewell! Ashiee session terminated.[/yellow]")
                    break
                elif cmd == "/clear":
                    console.clear()
                    render_banner(config, agent.session_id)
                    continue
                elif cmd == "/help":
                    help_table = Table(title="Ashiee Slash Commands", border_style="cyan")
                    help_table.add_column("Command", style="bold yellow")
                    help_table.add_column("Description")
                    help_table.add_row("/help", "Show this cheat sheet")
                    help_table.add_row("/skills", "Show all discovered skills")
                    help_table.add_row("/tools", "List all registered tools")
                    help_table.add_row("/plan", "Instruct Ashiee to formulate a thorough plan")
                    help_table.add_row("/session", "Display session details and transcript paths")
                    help_table.add_row("/clear", "Clear terminal display")
                    help_table.add_row("/exit", "Terminate the session")
                    console.print(help_table)
                    continue
                elif cmd == "/skills":
                    summary = agent.skill_manager.get_skill_summary_prompt()
                    console.print(Panel(summary, title="[bold green]Active Skills Catalog[/bold green]", border_style="green"))
                    continue
                elif cmd == "/tools":
                    t_table = Table(title="Registered Ashiee Tools", border_style="blue")
                    t_table.add_column("Tool Name", style="bold cyan")
                    t_table.add_column("Description")
                    for t in agent.tools.list_tools():
                        t_table.add_row(t.name, t.description)
                    console.print(t_table)
                    continue
                elif cmd == "/session":
                    console.print(f"[bold]Session ID:[/bold] {agent.session_id}")
                    console.print(f"[bold]Session Directory:[/bold] {agent.session_dir}")
                    console.print(f"[bold]Transcript Log:[/bold] {agent.transcript.compact_path}")
                    continue
                elif cmd == "/plan":
                    user_input = "Please formulate a detailed step-by-step architectural plan before proceeding with execution."

            # Execute turn with animated status
            with console.status("[bold cyan]Ashiee is reasoning...[/bold cyan]", spinner="dots"):
                response = await agent.execute_turn(user_input)

            # Render assistant markdown
            console.print(Markdown(response))
            console.print("")

        except (KeyboardInterrupt, EOFError):
            console.print("\n[yellow]Session interrupted. Goodbye![yellow]")
            break


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--provider", type=click.Choice(["gemini", "openai", "mock"]), default="gemini", help="LLM Provider to use.")
@click.option("--model", default=None, help="LLM model name.")
@click.option("--workspace", default=None, help="Workspace directory root.")
def cli(ctx, provider, model, workspace):
    """Ashiee: The Autonomous AI-First Pair Programmer & Agentic Runtime."""
    if ctx.invoked_subcommand is None:
        cfg = AshieeConfig()
        if workspace:
            cfg.workspace_root = Path(workspace).resolve()
        cfg.llm.provider = ModelProvider(provider)
        if model:
            cfg.llm.model_name = model
        asyncio.run(run_repl(cfg))


@cli.command()
@click.argument("prompt")
@click.option("--workspace", default=None)
@click.option("--provider", default="gemini")
def run(prompt: str, workspace: str, provider: str):
    """Execute a single-shot task autonomously in the workspace."""
    cfg = AshieeConfig()
    if workspace:
        cfg.workspace_root = Path(workspace).resolve()
    cfg.llm.provider = ModelProvider(provider)
    agent = AshieeAgent(cfg)
    setup_agent_listeners(agent)

    async def _run():
        res = await agent.execute_turn(prompt)
        console.print(Markdown(res))

    asyncio.run(_run())


@cli.command()
@click.option("--port", default=8000, help="Port to run the Web Canvas server on.")
@click.option("--host", default="127.0.0.1", help="Host interface.")
def serve(port: int, host: str):
    """Launch the Ashiee Web Canvas Desktop Dashboard."""
    import uvicorn
    console.print(f"[bold green]Starting Ashiee Desktop Canvas on http://{host}:{port}...[/bold green]")
    uvicorn.run("ashiee.server.app:app", host=host, port=port, reload=False)


@cli.command()
def gui():
    """Launch the native desktop window application."""
    from ashiee.gui.app import launch_gui
    launch_gui()


if __name__ == "__main__":
    cli()
