from typing import Protocol


class Command(Protocol):
    name: str
    description: str

    async def execute(
        self,
        args: list[str],
        context: dict | None = None,
    ) -> None: ...
