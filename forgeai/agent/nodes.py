from collections.abc import Callable
from typing import Any

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, SystemMessage
from rich.prompt import Confirm

from forgeai.agent.approval import request_tool_approval
from forgeai.agent.modes import AgentMode
from forgeai.agent.restrictions import (
    filter_tools_by_mode,
    get_mode_switch_suggestion,
    validate_tool_execution,
)
from forgeai.agent.state import AgentState
from forgeai.config.prompts import SYSTEM_PROMPT
from forgeai.config.settings import settings
from forgeai.ui.console import console


def create_agent_node(
    llm: BaseChatModel,
    tools: list,
    mcp_tools: list,
    mcp_context: str = "",
) -> Callable:
    def agent_node(state: AgentState) -> AgentState:
        current_mode_str = state.get("current_mode", "CODE")
        current_mode = AgentMode[current_mode_str]

        mode_prompt = f"\n\nCURRENT OPERATIONAL MODE: {current_mode.value}\n"

        if current_mode == AgentMode.ARCHITECT:
            mode_prompt += (
                "You are in ARCHITECT mode. Focus on planning and design.\n"
                f"You may write only inside '{settings.plans_directory}'.\n"
                "Use the write_file tool for plans and design documents.\n"
                "Do not use shell commands to create files."
            )

        elif current_mode == AgentMode.ASK:
            mode_prompt += (
                "You are in ASK mode. You can answer questions and perform research.\n"
                "You cannot modify files or execute shell commands."
            )

        else:
            mode_prompt += (
                "You are in CODE mode. You have full access to the available tools."
            )

        system_prompt = f"{SYSTEM_PROMPT}{mode_prompt}"

        if mcp_context:
            system_prompt += f"\n\n{mcp_context}"

        filtered_tools = filter_tools_by_mode(
            tools,
            current_mode,
            mcp_tools,
        )

        llm_with_tools = llm.bind_tools(filtered_tools)

        messages = state.get("messages", [])

        processed_messages = []

        for message in messages:
            if isinstance(message, SystemMessage):
                continue

            content = getattr(message, "content", "")

            if isinstance(content, str) and len(content) > 10000:
                message.content = content[:10000] + "... (truncated)"

            processed_messages.append(message)

        if len(processed_messages) > 15:
            processed_messages = processed_messages[-15:]

        final_messages = [
            SystemMessage(content=system_prompt),
            *processed_messages,
        ]

        response: AIMessage = llm_with_tools.invoke(final_messages)

        return {
            "messages": [response],
            "iteration_count": state.get("iteration_count", 0) + 1,
        }

    return agent_node


def should_continue(state: AgentState) -> str:
    messages = state.get("messages", [])

    if not messages:
        return "end"

    if state.get("iteration_count", 0) >= settings.max_iterations:
        return "end"

    last_message: Any = messages[-1]

    if hasattr(last_message, "tool_calls") and last_message.tool_calls:
        if settings.approval_required:
            return "request_approval"

        return "continue"

    return "end"


async def approval_node(state: AgentState) -> AgentState:
    messages = state.get("messages", [])

    if not messages:
        return state

    last_message = messages[-1]

    current_mode_str = state.get("current_mode", "CODE")
    current_mode = AgentMode[current_mode_str]

    all_approved = True

    for tool_call in last_message.tool_calls:
        tool_name = tool_call["name"]
        tool_args = tool_call["args"]

        is_valid, error_msg = validate_tool_execution(
            tool_name,
            tool_args,
            current_mode,
        )

        if not is_valid:
            suggestion = get_mode_switch_suggestion(
                tool_name,
                tool_args,
                current_mode,
            )

            if suggestion:
                target_mode, _ = suggestion

                console.print(
                    f"\n[bold yellow]⚠ Mode Restriction:[/bold yellow] " f"{error_msg}"
                )

                if Confirm.ask(
                    f"Switch to [bold cyan]{target_mode.value}[/bold cyan] mode?",
                    default=True,
                ):
                    current_mode = target_mode
                    current_mode_str = target_mode.value

                    console.print(
                        f"[green]✓[/green] Mode switched to "
                        f"[bold]{current_mode_str}[/bold]"
                    )

                    is_valid = True
                else:
                    all_approved = False
                    continue

            else:
                console.print(f"\n[red]✗[/red] {error_msg}")
                all_approved = False
                continue

        approved = await request_tool_approval(
            tool_name,
            tool_args,
            description=tool_call.get("description", ""),
        )

        if not approved:
            all_approved = False
            break

        if tool_name == "switch_mode":
            target_mode = tool_args.get("target_mode", "").upper()

            if target_mode in [mode.value for mode in AgentMode]:
                current_mode_str = target_mode
                current_mode = AgentMode[target_mode]

                console.print(
                    f"[green]✓[/green] Agent mode switched to "
                    f"[bold cyan]{current_mode_str}[/bold cyan]"
                )

    return {
        "approval_granted": all_approved,
        "pending_approval": False,
        "current_mode": current_mode_str,
    }


__all__ = [
    "approval_node",
    "create_agent_node",
    "should_continue",
]
