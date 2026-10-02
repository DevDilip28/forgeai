import json

from rich.panel import Panel
from rich.prompt import Prompt
from rich.syntax import Syntax

from forgeai.ui.console import console

MAX_TRUNCATION_LENGTH = 200
MAX_SUMMARY_PARAMS = 2


async def request_tool_approval(
    tool_name: str,
    tool_args: dict,
    description: str = "",
) -> bool:
    console.print()
    console.print("[bold yellow]Tool Execution Pending Approval[/bold yellow]")
    console.print()
    console.print(f"  [cyan]Tool:[/cyan] {tool_name}")

    if description:
        console.print(f"  [cyan]Action:[/cyan] {description}")

    param_summary = _get_param_summary(tool_args)
    console.print(f"  [cyan]Parameters:[/cyan] {param_summary}")

    while True:
        console.print()
        response = Prompt.ask(
            "[yellow]Approve?[/yellow]",
            choices=["y", "n", "d"],
            default="y",
        )

        if response == "y":
            return True

        if response == "n":
            console.print("[red]✗[/red] Tool execution cancelled")
            return False

        if response == "d":
            _show_full_parameters(tool_name, tool_args)


def _get_param_summary(tool_args: dict) -> str:
    if not tool_args:
        return "none"

    param_names = list(tool_args.keys())

    if len(param_names) <= MAX_SUMMARY_PARAMS:
        return ", ".join(param_names)

    return (
        f"{', '.join(param_names[:MAX_SUMMARY_PARAMS])}, "
        "... (use 'd' to view details)"
    )


def _show_full_parameters(tool_name: str, tool_args: dict) -> None:
    console.print()
    console.print("[bold]Full Parameters:[/bold]")
    console.print()

    truncated_args = {}

    for key, value in tool_args.items():
        if isinstance(value, str) and len(value) > MAX_TRUNCATION_LENGTH:
            truncated_args[key] = f"{value[:MAX_TRUNCATION_LENGTH]}... (truncated)"
        else:
            truncated_args[key] = value

    json_str = json.dumps(truncated_args, indent=2)
    syntax = Syntax(
        json_str,
        "json",
        theme="monokai",
        line_numbers=False,
    )

    console.print(Panel(syntax, border_style="dim"))


__all__ = ["request_tool_approval"]
