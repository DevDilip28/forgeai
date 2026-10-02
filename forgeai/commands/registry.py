from typing import ClassVar

from rich.table import Table

from forgeai.commands.base import Command
from forgeai.ui.console import console


class CommandRegistry:
    _commands: ClassVar[dict[str, Command]] = {}

    @classmethod
    def register(cls, command: Command) -> None:
        cls._commands[command.name] = command

    @classmethod
    def get_command(cls, name: str) -> Command | None:
        return cls._commands.get(name)

    @classmethod
    async def execute(cls, input_str: str, context: dict | None = None) -> bool:
        if not input_str.startswith("/"):
            return False

        parts = input_str[1:].split()
        if not parts:
            return False

        cmd_name = parts[0].lower()
        args = parts[1:]

        command = cls.get_command(cmd_name)

        if command:
            await command.execute(args, context=context)
            return True

        console.print(f"[red]Unknown command: /{cmd_name}[/red]")
        console.print("[dim]Type /help for a list of available commands.[/dim]")
        return True

    @classmethod
    def list_commands(cls) -> list[Command]:
        return sorted(cls._commands.values(), key=lambda command: command.name)

    @classmethod
    def show_help(cls) -> None:
        table = Table(
            title="[bold cyan]Available Commands[/bold cyan]",
            show_header=True,
            header_style="bold white",
            border_style="cyan",
            expand=False,
        )

        table.add_column("Command", style="cyan")
        table.add_column("Description", style="white")

        for command in cls.list_commands():
            table.add_row(f"/{command.name}", command.description)

        console.print(table)
        console.print()
