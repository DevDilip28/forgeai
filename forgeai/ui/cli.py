import rich_click as click

from langchain_core.messages import HumanMessage

from rich.console import Console
from rich.panel import Panel

from forgeai.agent.graph import agent_graph

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
            "[bold]ForgeAI[/bold]\n" "Autonomous AI Coding Agent",
            title="Welcome",
        )
    )

    while True:
        user_input = console.input("\n[bold cyan]ForgeAI> [/bold cyan]").strip()

        if not user_input:
            continue

        if user_input.lower() in {"exit", "quit"}:
            console.print("[yellow]Exiting ForgeAI...[/yellow]")
            break

        try:
            result = agent_graph.invoke(
                {"messages": [HumanMessage(content=user_input)]}
            )

            response = result["messages"][-1]

            console.print(
                f"\n[bold green]ForgeAI:[/bold green]\n" f"{response.content}"
            )

        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
