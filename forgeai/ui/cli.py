from langchain.messages import HumanMessage
import rich_click as click
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
            result = agent_graph.invoke(
                {"messages": [HumanMessage(content=user_input)]}
            )

            response = result["messages"][-1]

            console.print(
                f"\n[bold green]ForgeAI:[/bold green]\n" f"{response.content}"
            )

        except Exception as error:
            console.print(f"[bold red]Error:[/bold red] {error}")
