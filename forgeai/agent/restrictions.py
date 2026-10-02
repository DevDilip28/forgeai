from forgeai.agent.modes import (
    AgentMode,
    get_mode_config,
    is_path_in_plans_dir,
    validate_file_path,
)
from forgeai.config.settings import settings


def filter_tools_by_mode(
    tools: list,
    mode: AgentMode,
    mcp_tools: list,
) -> list:
    if mode in (AgentMode.CODE, AgentMode.ARCHITECT):
        return tools + mcp_tools

    if mode == AgentMode.ASK:
        return mcp_tools

    return tools + mcp_tools


def validate_tool_execution(
    tool_name: str,
    tool_args: dict,
    mode: AgentMode,
) -> tuple[bool, str]:
    config = get_mode_config(mode)

    if tool_name == "switch_mode":
        return True, ""

    if tool_name == "write_file" and not config.allows_file_write:
        return (
            False,
            f"File write operations are not allowed in " f"{mode.value} mode.",
        )

    if tool_name == "execute_shell_command" and not config.allows_shell_exec:
        return (
            False,
            f"Shell execution is not allowed in " f"{mode.value} mode.",
        )

    if config.restricted_to_plans_dir and tool_name == "write_file":
        path = tool_args.get("path", "")

        if path:
            valid, error = validate_file_path(
                path,
                mode,
                settings.plans_directory,
            )

            if not valid:
                return False, error

    return True, ""


def get_mode_switch_suggestion(
    tool_name: str,
    tool_args: dict,
    current_mode: AgentMode,
) -> tuple[AgentMode, str] | None:

    if current_mode == AgentMode.ASK:
        if tool_name in {
            "write_file",
            "execute_shell_command",
        }:
            return (
                AgentMode.CODE,
                f"{tool_name} requires CODE mode.",
            )

    if current_mode == AgentMode.ARCHITECT:
        if tool_name == "write_file":
            path = tool_args.get("path", "")

            if path and not is_path_in_plans_dir(
                path,
                settings.plans_directory,
            ):
                return (
                    AgentMode.CODE,
                    "Writing outside the planning directory " "requires CODE mode.",
                )

    return None
