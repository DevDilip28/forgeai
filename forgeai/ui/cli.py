import rich_click as click
from rich.console import Console
from rich.panel import Panel

console = Console()

@click.group()
def cli():
    """ForgeAI - Autonomous AI Coding Agent."""
    pass

@cli.command()
def chat():
    """Start an interactive ForgeAI session."""

    console.print(
        Panel(
            "[bold]ForgeAI[/bold] - Autonomous AI Coding Agent\n\n",
            title="Welcome to ForgeAI",
        )
    )

    while True:
        user_input = console.input("\n[bold cyan]ForgeAI> [/bold cyan]")

        if user_input.lower() in {"exit", "quit"}:
            console.print("\n[bold red]Exiting ForgeAI...[/bold red]")
            break

        console.print(f"You said: {user_input}")

