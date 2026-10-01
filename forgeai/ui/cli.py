import rich_click as click
from rich.console import Console
from rich.panel import Panel

from forgeai.agent.llm import llm_client

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

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            console.print("\n[bold red]Exiting ForgeAI...[/bold red]")
            break

        try:
            response = llm_client.generate_response(user_input)

            console.print(f"\n[bold green]ForgeAI:\n{response}")

        except Exception as error:
            console.print(f"\n[bold red]Error: {error}[/bold red]")
