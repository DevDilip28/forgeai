from rich.align import Align
from rich.panel import Panel
from rich.rule import Rule
from rich.table import Table, box
from rich.text import Text

from forgeai.agent.metrics import MetricsManager
from forgeai.commands.registry import CommandRegistry
from forgeai.config.settings import settings
from forgeai.tools.mcp import _active_mcp_tools_info, get_mcp_status
from forgeai.ui.console import console


class HelpCommand:
    name = "help"
    description = "Show available slash commands"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        CommandRegistry.show_help()


class AboutCommand:
    name = "about"
    description = "Show application information"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        banner_text = Text.assemble(
            ("FORGEAI", "bold white"),
            (" - AI Coding Agent\n", "bold cyan"),
            ("Powered by LangChain, LangGraph & MCP", "dim cyan"),
        )

        panel = Panel(
            Align.left(banner_text),
            border_style="cyan",
            width=60,
            padding=(1, 2),
        )

        console.print(panel)
        console.print()


class ConfigCommand:
    name = "config"
    description = "Show current configuration"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        table = Table(
            title="[bold cyan]Configuration[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            padding=(0, 1),
        )

        table.add_column("Setting", style="cyan", no_wrap=True)
        table.add_column("Value", style="white")

        if context and "get_state" in context:
            state = context["get_state"]()
            current_mode = state.get("current_mode", "CODE")
            table.add_row(
                "Current Mode",
                f"[bold cyan]{current_mode}[/bold cyan]",
            )

        table.add_row("Model", f"[green]{settings.model_name}[/green]")
        table.add_row("Temperature", f"[yellow]{settings.temperature}[/yellow]")
        table.add_row("Max Tokens", f"[yellow]{settings.max_tokens}[/yellow]")
        table.add_row(
            "Max Iterations",
            f"[yellow]{settings.max_iterations}[/yellow]",
        )
        table.add_row(
            "Approval Required",
            "[green]Yes[/green]" if settings.approval_required else "[red]No[/red]",
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

        console.print(table)
        console.print()


class MCPsCommand:
    name = "mcps"
    description = "Show active MCP servers and tool details"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        status = get_mcp_status()
        mcp_loaded = status["loaded"]

        title = f"[bold cyan]Active MCP Servers ({mcp_loaded})[/bold cyan]"

        if mcp_loaded == 0:
            console.print(
                Panel(
                    "[dim]No active MCP servers found.[/dim]",
                    title=title,
                    border_style="cyan",
                    width=60,
                )
            )
            return

        for server in status["servers"]:
            name = server["name"]
            command = server["command"]
            tool_count = server["tools"]

            table = Table(
                box=box.SIMPLE,
                show_edge=False,
                padding=(0, 1),
                expand=True,
            )

            table.add_column("Property", style="dim", width=15)
            table.add_column("Value", style="white")

            table.add_row("Command", command)
            table.add_row("Tool Count", str(tool_count))

            tools_info = _active_mcp_tools_info.get(name, [])

            if tools_info:
                table.add_row("", "")
                table.add_row("[cyan]Tools[/cyan]", "")

                for tool_info in tools_info:
                    table.add_row(
                        "",
                        f"[bold]{tool_info['name']}[/bold]: "
                        f"{tool_info['description']}",
                    )

            console.print(
                Panel(
                    table,
                    title=f"[bold green]{name}[/bold green]",
                    border_style="dim",
                    expand=False,
                )
            )
            console.print()


class ModeCommand:
    name = "mode"
    description = "Switch agent operational mode (code, architect, ask)"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        if not args:
            current_mode = "unknown"

            if context and "get_state" in context:
                state = context["get_state"]()
                current_mode = state.get("current_mode", "CODE")

            console.print(
                f"[yellow]Current mode:[/yellow] "
                f"[bold cyan]{current_mode}[/bold cyan]"
            )
            console.print("[yellow]Usage:[/yellow] /mode <code|architect|ask>")
            return

        mode_name = args[0].upper()

        if mode_name not in ["CODE", "ARCHITECT", "ASK"]:
            console.print(f"[red]Invalid mode: {args[0]}[/red]")
            console.print("[yellow]Available modes:[/yellow] code, architect, ask")
            return

        if context and "update_state" in context:
            await context["update_state"]({"current_mode": mode_name})
            console.print(
                f"[green]✓[/green] Switched to "
                f"[bold cyan]{mode_name}[/bold cyan] mode"
            )
        else:
            console.print(
                "[red]Error: Could not update agent mode " "in this context.[/red]"
            )


class MetricsCommand:
    name = "metrics"
    description = "Show aggregate session metrics"

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None:
        if (
            not context
            or "metrics_manager" not in context
            or "thread_id" not in context
        ):
            console.print("[red]Error: Metrics context not available.[/red]")
            return

        metrics_manager: MetricsManager = context["metrics_manager"]
        thread_id: str = context["thread_id"]

        summary = metrics_manager.get_session_summary(thread_id)

        if not summary or not summary.get("total_requests"):
            console.print("[yellow]No metrics available for this session yet.[/yellow]")
            return

        table = Table(
            title=f"[bold cyan]Aggregate Metrics: {thread_id}[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            box=box.ROUNDED,
        )

        table.add_column("Metric", style="dim")
        table.add_column("Value", style="white")

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
            table.add_row("Avg TTFT", f"{ttft:.2f}s")

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

        cached = summary.get("total_cached_tokens", 0)

        if cached > 0:
            table.add_row(
                "Total Cached Tokens",
                str(cached),
            )

        console.print(table)
        console.print()


def register_core_commands() -> None:
    CommandRegistry.register(HelpCommand())
    CommandRegistry.register(AboutCommand())
    CommandRegistry.register(ConfigCommand())
    CommandRegistry.register(MCPsCommand())
    CommandRegistry.register(ModeCommand())
    CommandRegistry.register(MetricsCommand())
