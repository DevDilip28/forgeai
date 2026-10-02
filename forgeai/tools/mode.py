from typing import Annotated

from langchain_core.tools import tool

from forgeai.agent.modes import AgentMode


@tool
def switch_mode(
    target_mode: Annotated[
        str,
        "The mode to switch to (CODE, ARCHITECT, or ASK)",
    ],
) -> str:
    """Request a transition to the specified agent mode."""
    mode_name = target_mode.upper()

    if mode_name not in [mode.value for mode in AgentMode]:
        return (
            f"Error: Invalid mode '{target_mode}'. "
            "Available modes: CODE, ARCHITECT, ASK."
        )

    return f"Requesting transition to {mode_name} mode..."


mode_tools = [switch_mode]


__all__ = [
    "mode_tools",
    "switch_mode",
]
