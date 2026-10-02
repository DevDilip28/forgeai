import asyncio
import time
from typing import Any

import rich_click as click
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from rich.align import Align
from rich.columns import Columns
from rich.console import Group
from rich.live import Live
from rich.markdown import Markdown
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.rule import Rule
from rich.table import Table, box
from rich.text import Text

from forgeai.agent.graph import create_agent_graph
from forgeai.agent.metrics import ChatMetrics, MetricsManager
from forgeai.commands.registry import CommandRegistry
from forgeai.commands.core import register_core_commands
from forgeai.config.settings import settings
from forgeai.tools.mcp import get_mcp_status
from forgeai.ui.console import console

click.rich_click.USE_RICH_MARKUP = True
click.rich_click.SHOW_ARGUMENTS = True
click.rich_click.GROUP_ARGUMENTS_OPTIONS = True
click.rich_click.STYLE_ERRORS_SUGGESTION = "magenta italic"
click.rich_click.STYLE_OPTION = "bold cyan"
click.rich_click.STYLE_ARGUMENT = "bold yellow"
click.rich_click.STYLE_COMMAND = "bold green"

PANEL_WIDTH_SMALL: int = 60
PANEL_WIDTH_MED: int = 70

PADDING_NORMAL: tuple[int, int] = (1, 2)
PADDING_WIDE: tuple[int, int] = (1, 4)

def print_banner() -> None:
    """Display the ForgeAI banner."""

    banner_text = Text.assemble(
        ("FORGEAI", "bold white"),
        (" - Autonomous Coding Agent\n", "bold cyan"),
        ("Powered by LangGraph, LangChain & MCP", "dim cyan"),
    )

    banner_panel = Panel(
        Align.center(banner_text),
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
        padding=PADDING_NORMAL,
    )

    console.print(Align.center(banner_panel))


def _get_session_table(
    thread_id: str,
    mode: str,
    *,
    stream: bool,
) -> Table:
    """Build the session information table."""

    mode_colors = {
        "CODE": "green",
        "ASK": "blue",
        "ARCHITECT": "magenta",
    }

    mode_style = mode_colors.get(mode, "cyan")

    table = Table.grid(padding=(0, 2))

    table.add_column(style="dim", justify="right")
    table.add_column(style="cyan")

    table.add_row("Model", settings.model_name)

    table.add_row(
        "Mode",
        f"[{mode_style}]{mode}[/{mode_style}]",
    )

    table.add_row("Thread", thread_id)

    table.add_row(
        "Working Dir",
        str(settings.working_directory),
    )

    table.add_row(
        "Streaming",
        "Enabled" if stream else "Disabled",
    )

    return table


def _get_mcp_table() -> tuple[Table, int]:
    """Build MCP server information table."""

    status = get_mcp_status()

    table = Table(
        box=box.SIMPLE_HEAD,
        show_edge=False,
        padding=(0, 1),
        expand=True,
    )

    table.add_column("Server", style="cyan")
    table.add_column("Command", justify="right", style="dim")

    if status["loaded"] > 0:
        for server in status["servers"]:
            table.add_row(
                server["name"],
                server["command"],
            )
    else:
        table.add_row(
            "[dim]No active MCP servers[/dim]",
            "",
        )

    return table, status["loaded"]


def _print_session_info(
    thread_id: str,
    mode: str = "CODE",
    *,
    stream: bool,
) -> None:
    """Display current ForgeAI session information."""

    session_table = _get_session_table(
        thread_id,
        mode,
        stream=stream,
    )

    session_panel = Panel(
        session_table,
        title="[bold cyan]ForgeAI Session[/bold cyan]",
        border_style="cyan",
        width=PANEL_WIDTH_SMALL,
    )

    console.print(Align.center(session_panel))

    # MCP information
    mcp_table, mcp_loaded = _get_mcp_table()

    if mcp_loaded > 0:
        mcp_panel = Panel(
            mcp_table,
            title=f"[bold cyan]MCP Servers ({mcp_loaded})[/bold cyan]",
            border_style="cyan",
            width=PANEL_WIDTH_SMALL,
        )

        console.print(Align.center(mcp_panel))

    console.print()


@click.group(invoke_without_command=True)
@click.pass_context
@click.version_option(
    version="1.0.0",
    prog_name="forgeai",
)
def cli(ctx: click.Context) -> None:
    """ForgeAI - Autonomous Coding Agent.

    Build, modify, debug and understand software using
    LangGraph, MCP and persistent agent state.
    """

    register_core_commands()

    if ctx.invoked_subcommand is None:
        print_banner()

        welcome_panel = Panel(
            "[bold white]Welcome to ForgeAI![/bold white]\n\n"
            "[dim]Available commands:[/dim]\n"
            "  [cyan]forgeai chat[/cyan]     - Start interactive coding session\n"
            "  [cyan]forgeai history[/cyan]  - View conversation history\n"
            "  [cyan]forgeai config[/cyan]   - Show configuration\n\n"
            "[dim]Inside chat:[/dim]\n"
            "  [yellow]/help[/yellow]      - Show slash commands\n"
            "  [yellow]/mode[/yellow]      - Change agent mode\n"
            "  [yellow]/config[/yellow]    - Show configuration\n"
            "  [yellow]/mcps[/yellow]      - Show MCP tools\n"
            "  [yellow]/metrics[/yellow]   - Show session metrics\n"
            "  [yellow]/exit[/yellow]      - Exit session\n\n"
            "[dim]For help:[/dim] [yellow]forgeai --help[/yellow]",
            border_style="cyan",
            padding=PADDING_WIDE,
            width=PANEL_WIDTH_SMALL,
        )

        console.print(Align.center(welcome_panel))


@cli.command()
@click.argument("message", required=False)
@click.option(
    "--thread-id",
    "-t",
    help="Thread ID for conversation continuity",
    default="default",
)
@click.option(
    "--stream/--no-stream",
    default=True,
    help="Stream responses in real-time",
)
def chat(
    message: str | None,
    thread_id: str,
    *,
    stream: bool,
) -> None:
    """Start an interactive ForgeAI coding session."""

    asyncio.run(
        _chat(
            message,
            thread_id,
            stream=stream,
        ),
    )


async def _chat(
    message: str | None,
    thread_id: str,
    *,
    stream: bool,
) -> None:
    """Initialize and run a ForgeAI session."""

    print_banner()

    async with AsyncSqliteSaver.from_conn_string(
        settings.checkpoint_db,
    ) as checkpointer:

        status = console.status(
            "[bold cyan]Initializing ForgeAI agent...[/bold cyan]",
            spinner="dots",
        )

        status.start()

        try:
            async with create_agent_graph(
                checkpointer=checkpointer,
            ) as agent:

                status.stop()

                config: dict = {
                    "configurable": {
                        "thread_id": thread_id,
                    },
                }

                state = await agent.aget_state(config)

                current_mode = (
                    state.values.get("current_mode", "CODE") if state.values else "CODE"
                )

                _print_session_info(
                    thread_id,
                    mode=current_mode,
                    stream=stream,
                )

                metrics_manager = MetricsManager()

                if message is None:
                    await _interactive_chat_loop(
                        agent,
                        config,
                        metrics_manager,
                        thread_id,
                        stream=stream,
                    )
                else:
                    await _process_message(
                        agent,
                        message,
                        config,
                        stream=stream,
                        metrics_manager=metrics_manager,
                        thread_id=thread_id,
                        mode=current_mode,
                    )

                    _print_metrics_summary(
                        metrics_manager,
                        thread_id,
                    )

        finally:
            status.stop()


async def _interactive_chat_loop(
    agent: Any,
    config: dict,
    metrics_manager: MetricsManager,
    thread_id: str,
    *,
    stream: bool,
) -> None:
    """Run the interactive terminal chat loop."""

    console.print(
        Align.center(
            Panel(
                "[dim]Type your request and press Enter.[/dim]\n\n"
                "[dim]Examples:[/dim]\n"
                "  [cyan]Create a FastAPI endpoint for user authentication[/cyan]\n"
                "  [cyan]Find the bug in this project[/cyan]\n"
                "  [cyan]Explain how this code works[/cyan]\n"
                "  [cyan]Add tests for the authentication module[/cyan]\n\n"
                "[dim]Commands:[/dim] "
                "[yellow]/help[/yellow] "
                "[yellow]/mode[/yellow] "
                "[yellow]/config[/yellow] "
                "[yellow]/mcps[/yellow] "
                "[yellow]/metrics[/yellow] "
                "[yellow]/exit[/yellow]",
                border_style="dim",
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )

    console.print()

    session_start = time.time()

    while True:
        try:
            state = await agent.aget_state(config)

            current_mode = (
                state.values.get("current_mode", "CODE") if state.values else "CODE"
            )

            _print_header(
                "User",
                mode=current_mode,
            )

            prompt_text = "[bold green]> [/bold green]"

            message = console.input(prompt_text)

            if message.lower() in [
                "exit",
                "quit",
                "q",
                "/exit",
            ]:
                duration = time.time() - session_start

                _print_exit_screen(
                    metrics_manager,
                    thread_id,
                    duration,
                )

                break

            if not message.strip():
                continue

            async def get_current_state() -> dict:
                """Return current agent state."""

                state = await agent.aget_state(config)

                return state.values if state.values else {}

            async def update_state(
                new_values: dict,
            ) -> None:
                """Update agent state."""

                await agent.aupdate_state(
                    config,
                    new_values,
                    as_node="agent",
                )

            context = {
                "get_state": get_current_state,
                "update_state": update_state,
                "metrics_manager": metrics_manager,
                "thread_id": thread_id,
            }

            if message.startswith("/"):
                handled = await CommandRegistry.execute(
                    message,
                    context=context,
                )

                if handled:
                    continue

            await _process_message(
                agent,
                message,
                config,
                stream=stream,
                metrics_manager=metrics_manager,
                thread_id=thread_id,
                mode=current_mode,
            )

        except KeyboardInterrupt:
            console.print(
                "\n\n[dim]Use '/exit' to quit ForgeAI.[/dim]",
            )

        except EOFError:
            duration = time.time() - session_start

            _print_exit_screen(
                metrics_manager,
                thread_id,
                duration,
            )

            break


def _print_exit_screen(
    metrics_manager: MetricsManager,
    thread_id: str,
    duration: float,
) -> None:
    """Display session summary when ForgeAI exits."""

    summary = metrics_manager.get_session_summary(
        thread_id,
    )

    goodbye_text = Text.assemble(
        ("FORGEAI SESSION COMPLETE", "bold cyan"),
        (
            "\nSession closed successfully.",
            "italic dim",
        ),
    )

    minutes = int(duration // 60)
    seconds = int(duration % 60)

    duration_str = f"{minutes}m {seconds}s" if minutes > 0 else f"{seconds}s"

    stats = []

    if summary and summary.get("total_requests"):
        stats.append(
            Panel(
                Align.center(
                    f"[bold cyan]"
                    f"{summary['total_requests']}"
                    f"[/bold cyan]\n"
                    "[dim]Requests[/dim]",
                ),
                border_style="dim",
                width=20,
            ),
        )

        stats.append(
            Panel(
                Align.center(
                    f"[bold green]"
                    f"{summary.get('total_tokens', 0):,}"
                    f"[/bold green]\n"
                    "[dim]Tokens[/dim]",
                ),
                border_style="dim",
                width=20,
            ),
        )

        stats.append(
            Panel(
                Align.center(
                    f"[bold yellow]"
                    f"{duration_str}"
                    f"[/bold yellow]\n"
                    "[dim]Session[/dim]",
                ),
                border_style="dim",
                width=20,
            ),
        )

    console.print()
    console.print(Rule(style="dim"))
    console.print()

    console.print(
        Align.center(
            Panel(
                Align.center(goodbye_text),
                border_style="cyan",
                padding=(1, 2),
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )

    console.print()

    if stats:
        console.print(
            Align.center(
                Columns(
                    stats,
                    equal=True,
                    expand=False,
                ),
            ),
        )

        console.print()

    if summary and summary.get("total_requests"):
        _print_metrics_summary(
            metrics_manager,
            thread_id,
            hide_title=True,
        )

    console.print(
        Align.center(
            "[dim]ForgeAI • Autonomous Coding Agent[/dim]",
        ),
    )

    console.print()


def _print_metrics_summary(
    metrics_manager: MetricsManager,
    thread_id: str,
    *,
    hide_title: bool = False,
) -> None:
    """Display aggregate session metrics."""

    summary = metrics_manager.get_session_summary(
        thread_id,
    )

    if not summary or not summary.get("total_requests"):
        return

    table = Table(
        title=(
            "[bold cyan]Session Metrics Summary[/bold cyan]" if not hide_title else None
        ),
        show_header=True,
        header_style="bold white",
        border_style="cyan",
        box=box.ROUNDED,
    )

    table.add_column(
        "Metric",
        style="dim",
    )

    table.add_column(
        "Value",
        style="white",
    )

    table.add_row(
        "Total Requests",
        str(summary["total_requests"]),
    )

    table.add_row(
        "Total Latency",
        f"{summary['total_latency']:.2f}s",
    )

    table.add_row(
        "Avg Latency",
        f"{summary['avg_latency']:.2f}s",
    )

    ttft = summary.get("avg_ttft")

    if ttft is not None:
        table.add_row(
            "Avg TTFT",
            f"{ttft:.2f}s",
        )

    table.add_row(
        Rule(style="dim"),
        Rule(style="dim"),
    )

    table.add_row(
        "Total Input Tokens",
        str(summary["total_input_tokens"]),
    )

    table.add_row(
        "Total Output Tokens",
        str(summary["total_output_tokens"]),
    )

    table.add_row(
        "Total Tokens",
        str(summary["total_tokens"]),
    )

    cached = summary.get(
        "total_cached_tokens",
        0,
    )

    if cached > 0:
        table.add_row(
            "Total Cached Tokens",
            str(cached),
        )

    console.print(
        Align.center(
            table,
            width=PANEL_WIDTH_MED,
        ),
    )

    console.print()


def _print_request_metrics(
    metrics: ChatMetrics,
) -> None:
    """Display metrics for one request."""

    latency = f"{metrics.request_latency:.2f}s"

    ttft = (
        f"{metrics.first_token_latency:.2f}s" if metrics.first_token_latency else "N/A"
    )

    usage_parts = []

    if metrics.input_tokens > 0:
        usage_parts.append(
            f"{metrics.input_tokens} in",
        )

    if metrics.output_tokens > 0:
        usage_parts.append(
            f"{metrics.output_tokens} out",
        )

    if metrics.cached_tokens > 0:
        usage_parts.append(
            f"{metrics.cached_tokens} cached",
        )

    usage_str = (
        f"Usage: {metrics.total_tokens} tokens " f"({', '.join(usage_parts)})"
        if usage_parts
        else "Usage: N/A"
    )

    metrics_text = Text.assemble(
        (" Latency: ", "dim"),
        (latency, "cyan dim"),
        (" | TTFT: ", "dim"),
        (ttft, "cyan dim"),
        (" | ", "dim"),
        (f"{usage_str} ", "dim"),
    )

    console.print(
        Rule(
            metrics_text,
            style="dim",
            align="right",
        ),
    )


def _print_header(
    role: str,
    mode: str | None = None,
) -> None:
    """Display a role header."""

    if role.lower() == "user":
        mode_colors = {
            "CODE": "green",
            "ASK": "blue",
            "ARCHITECT": "magenta",
        }

        style = mode_colors.get(
            mode or "CODE",
            "green",
        )

        label = f" {mode or 'USER'} "

    else:
        style = "cyan"
        label = " Assistant "

    console.print()

    console.print(
        Rule(
            f"[bold white on {style}]" f" {label} " f"[/bold white on {style}]",
            style=style,
        ),
    )

    console.print()


class StreamingResponseHandler:
    """Handle streaming AI response rendering."""

    def __init__(self) -> None:
        self.full_content: str = ""

    def update(
        self,
        chunk: str,
    ) -> None:
        """Append a response chunk."""

        self.full_content += chunk

    def render(self) -> Group:
        """Render the current response."""

        if not self.full_content:
            return Group(
                Text(
                    "...",
                    style="dim",
                ),
            )

        return Group(
            Markdown(
                self.full_content,
            ),
        )


async def _handle_streaming_response(
    agent: Any,
    input_state: dict,
    config: dict,
    mode: str,
    start_time: float,
) -> tuple[float | None, dict]:
    """Handle streaming agent response."""

    _print_header(
        "Assistant",
        mode=mode,
    )

    ttft: float | None = None
    usage: dict = {}

    handler = StreamingResponseHandler()

    with Live(
        handler.render(),
        console=console,
        refresh_per_second=10,
    ) as live:

        async for event in agent.astream_events(
            input_state,
            config,
            version="v2",
        ):
            kind = event["event"]

            if kind == "on_chat_model_stream":

                if ttft is None:
                    ttft = time.time() - start_time

                content = event["data"]["chunk"].content

                if content:
                    handler.update(content)
                    live.update(
                        handler.render(),
                    )

            elif kind == "on_chat_model_end":

                output = event["data"].get(
                    "output",
                    {},
                )

                if (
                    hasattr(
                        output,
                        "usage_metadata",
                    )
                    and output.usage_metadata
                ):
                    usage = output.usage_metadata

            elif kind == "on_tool_start":

                tool_name = event["name"]

                live.stop()

                console.print(
                    f"\n[dim]┌─ Tool: " f"[cyan]{tool_name}" f"[/cyan][/dim]",
                )

            elif kind == "on_tool_end":

                console.print(
                    "[dim]└─ ✓ Completed[/dim]\n",
                )

                live.start()

            elif kind == "on_chain_start" and event["name"] == "approval":
                live.stop()

            elif kind == "on_chain_end" and event["name"] == "approval":
                live.start()

    console.print()

    return ttft, usage


async def _handle_static_response(
    agent: Any,
    input_state: dict,
    config: dict,
    mode: str,
) -> dict:
    """Handle non-streaming agent response."""

    with console.status(
        "[bold cyan]ForgeAI is working...[/bold cyan]",
        spinner="dots",
    ):
        result = await agent.ainvoke(
            input_state,
            config,
        )

    last_message = result["messages"][-1]

    usage: dict = {}

    if (
        hasattr(
            last_message,
            "usage_metadata",
        )
        and last_message.usage_metadata
    ):
        usage = last_message.usage_metadata

    mode_colors = {
        "CODE": "green",
        "ASK": "blue",
        "ARCHITECT": "magenta",
    }

    style = mode_colors.get(
        mode,
        "cyan",
    )

    console.print(
        Align.center(
            Panel(
                Markdown(
                    last_message.content,
                ),
                title=(
                    f"[bold white on {style}]" " Assistant " f"[/bold white on {style}]"
                ),
                border_style=style,
                padding=(1, 2),
                width=PANEL_WIDTH_MED,
            ),
        ),
    )

    console.print()

    return usage


async def _process_message(
    agent: Any,
    message: str,
    config: dict,
    *,
    stream: bool,
    metrics_manager: MetricsManager,
    thread_id: str,
    mode: str = "CODE",
) -> None:
    """Process one user request."""

    input_state: dict = {
        "messages": [
            HumanMessage(
                content=message,
            ),
        ],
        "iteration_count": 0,
        "working_directory": str(
            settings.working_directory,
        ),
        "tool_calls_made": [],
        "files_modified": [],
    }

    console.print()

    start_time = time.time()

    if stream:
        ttft, usage = await _handle_streaming_response(
            agent,
            input_state,
            config,
            mode,
            start_time,
        )

    else:
        ttft = None

        usage = await _handle_static_response(
            agent,
            input_state,
            config,
            mode,
        )

    total_latency = time.time() - start_time

    metrics = ChatMetrics(
        thread_id=thread_id,
        timestamp=start_time,
        request_latency=total_latency,
        first_token_latency=ttft,
        input_tokens=usage.get(
            "input_tokens",
            0,
        ),
        output_tokens=usage.get(
            "output_tokens",
            0,
        ),
        total_tokens=usage.get(
            "total_tokens",
            0,
        ),
        cached_tokens=usage.get(
            "cached_tokens",
            0,
        ),
    )

    metrics_manager.save_metrics(
        metrics,
    )

    _print_request_metrics(
        metrics,
    )


@cli.command()
@click.option(
    "--thread-id",
    "-t",
    help="Thread ID to show history for",
    default="default",
)
@click.option(
    "--limit",
    "-n",
    help="Number of checkpoints to show",
    default=10,
    type=int,
)
def history(
    thread_id: str,
    limit: int,
) -> None:
    """Show conversation history."""

    asyncio.run(
        _show_history(
            thread_id,
            limit,
        ),
    )


async def _show_history(
    thread_id: str,
    limit: int,
) -> None:
    """Display historical conversation states."""

    print_banner()

    with Progress(
        SpinnerColumn(),
        TextColumn(
            "[progress.description]{task.description}",
        ),
        transient=True,
    ) as progress:

        progress.add_task(
            description="Loading ForgeAI history...",
            total=None,
        )

        async with AsyncSqliteSaver.from_conn_string(
            settings.checkpoint_db,
        ) as checkpointer:

            config: dict = {
                "configurable": {
                    "thread_id": thread_id,
                },
            }

            checkpoints = [
                checkpoint async for checkpoint in checkpointer.alist(config)
            ]

    if not checkpoints:
        console.print(
            Align.center(
                Panel(
                    f"[yellow]No history found for "
                    f"thread '[cyan]{thread_id}"
                    f"[/cyan]'[/yellow]",
                    border_style="yellow",
                    width=PANEL_WIDTH_SMALL,
                ),
            ),
        )

        return

    console.print(
        Align.center(
            Panel(
                "[bold]ForgeAI Conversation History[/bold]\n"
                f"[dim]Thread:[/dim] "
                f"[cyan]{thread_id}[/cyan]\n"
                f"[dim]Total Checkpoints:[/dim] "
                f"[cyan]{len(checkpoints)}[/cyan]",
                border_style="cyan",
                width=PANEL_WIDTH_SMALL,
            ),
        ),
    )

    console.print()

    for i, checkpoint in enumerate(
        reversed(
            checkpoints[:limit],
        ),
        1,
    ):
        state = checkpoint.checkpoint["channel_values"]

        messages = state.get(
            "messages",
            [],
        )

        console.print(
            f"[bold cyan]Checkpoint {i}[/bold cyan]",
        )

        console.print()

        for msg in messages:
            role = msg.__class__.__name__

            content = getattr(
                msg,
                "content",
                "",
            )

            if role == "HumanMessage":
                console.print(
                    f"[bold green]User:[/bold green] " f"{content}",
                )

            elif role == "AIMessage":
                preview = content[:200]

                if len(content) > 200:
                    preview += "..."

                console.print(
                    f"[bold cyan]Assistant:[/bold cyan] " f"{preview}",
                )

            else:
                preview = content[:100]

                if len(content) > 100:
                    preview += "..."

                console.print(
                    f"[dim]{role}:[/dim] " f"{preview}",
                )

        console.print(
            Align.center(
                Rule(style="dim"),
                width=PANEL_WIDTH_SMALL,
            ),
        )

        console.print()


@cli.command()
def config() -> None:
    """Show ForgeAI configuration."""

    print_banner()

    table = Table(
        title="[bold cyan]ForgeAI Configuration[/bold cyan]",
        show_header=True,
        header_style="bold white",
        border_style="cyan",
        padding=(0, 1),
    )

    table.add_column(
        "Setting",
        style="cyan",
        no_wrap=True,
    )

    table.add_column(
        "Value",
        style="white",
    )

    table.add_row(
        "Default Mode",
        "[bold green]CODE[/bold green]",
    )

    table.add_row(
        "Model",
        f"[green]{settings.model_name}[/green]",
    )

    table.add_row(
        "Temperature",
        f"[yellow]{settings.temperature}[/yellow]",
    )

    table.add_row(
        "Max Tokens",
        f"[yellow]{settings.max_tokens}[/yellow]",
    )

    table.add_row(
        "Max Iterations",
        f"[yellow]{settings.max_iterations}[/yellow]",
    )

    table.add_row(
        "Approval Required",
        ("[green]Yes[/green]" if settings.approval_required else "[red]No[/red]"),
    )

    table.add_row(
        "Working Directory",
        f"[dim]{settings.working_directory}[/dim]",
    )

    table.add_row(
        "LangSmith Tracing",
        (
            "[green]Enabled[/green]"
            if settings.langsmith_tracing
            else "[red]Disabled[/red]"
        ),
    )

    table.add_row(
        "Checkpoint DB",
        f"[dim]{settings.checkpoint_db}[/dim]",
    )

    table.add_row(
        "Plans Directory",
        f"[dim]{settings.plans_directory}[/dim]",
    )

    table.add_row(
        "Log Level",
        f"[yellow]{settings.log_level}[/yellow]",
    )

    console.print(
        Align.center(table),
    )

    console.print()


if __name__ == "__main__":
    cli()


__all__: list[str] = ["cli"]
