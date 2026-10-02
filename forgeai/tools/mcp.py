import json
import shutil
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_core.tools import BaseTool
from langchain_mcp_adapters.client import MultiServerMCPClient
from mcp import StdioServerParameters

from forgeai.config.settings import settings
from forgeai.ui.console import console

_active_mcp_tool_counts: dict[str, int] = {}
_active_mcp_tools_info: dict[str, list[dict[str, str]]] = {}


def _find_executable(command: str) -> str:
    executable = shutil.which(command)

    if not executable:
        if command == "npx":
            executable = shutil.which("npx.cmd")
        elif command == "npm":
            executable = shutil.which("npm.cmd")

    if not executable:
        raise FileNotFoundError(f"Command '{command}' not found in PATH.")

    return executable


def get_mcp_server_params() -> dict[str, StdioServerParameters]:
    config_path = settings.mcp_config_path

    if not config_path.exists():
        return {}

    try:
        data = json.loads(config_path.read_text(encoding="utf-8"))
        mcp_servers = data.get("mcpServers", {})

        server_params: dict[str, StdioServerParameters] = {}

        for name, config in mcp_servers.items():
            command = config.get("command")
            args = config.get("args", [])

            if not command:
                continue

            try:
                executable = _find_executable(command)

                server_params[name] = StdioServerParameters(
                    command=executable,
                    args=args,
                    env=config.get("env"),
                )
            except FileNotFoundError:
                continue

        return server_params

    except Exception:
        return {}


@asynccontextmanager
async def load_mcp_tools() -> AsyncIterator[list[BaseTool]]:
    _active_mcp_tool_counts.clear()
    _active_mcp_tools_info.clear()

    server_params = get_mcp_server_params()

    if not server_params:
        yield []
        return

    all_tools: list[BaseTool] = []

    try:
        for name, params in server_params.items():
            client_config = {
                name: {
                    "command": params.command,
                    "args": params.args,
                    "transport": "stdio",
                    "env": params.env,
                }
            }

            try:
                client = MultiServerMCPClient(client_config)
                tools = await client.get_tools()

                _active_mcp_tool_counts[name] = len(tools)

                _active_mcp_tools_info[name] = [
                    {
                        "name": tool.name,
                        "description": tool.description,
                    }
                    for tool in tools
                ]

                all_tools.extend(tools)

            except Exception as e:
                console.print(f"[dim red]Error loading MCP {name}: {e}[/dim red]")

                _active_mcp_tool_counts[name] = 0

        yield all_tools

    finally:
        pass


def get_mcp_status() -> dict[str, Any]:
    status: dict[str, Any] = {
        "loaded": 0,
        "servers": [],
        "config_found": settings.mcp_config_path.exists(),
    }

    if not status["config_found"]:
        return status

    try:
        data = json.loads(settings.mcp_config_path.read_text(encoding="utf-8"))

        servers = data.get("mcpServers", {})
        status["loaded"] = len(servers)

        for name, config in servers.items():
            status["servers"].append(
                {
                    "name": name,
                    "command": config.get("command", "unknown"),
                    "tools": _active_mcp_tool_counts.get(name, 0),
                }
            )

    except Exception:
        return status

    return status


def get_mcp_context_prompt() -> str:
    if not _active_mcp_tools_info:
        return ""

    lines = ["\n## Active MCP Servers & Tools\n"]

    for server_name, tools in _active_mcp_tools_info.items():
        if not tools:
            continue

        lines.append(f"### Server: {server_name}")

        for tool_info in tools:
            lines.append(f"- **{tool_info['name']}**: {tool_info['description']}")

        lines.append("")

    return "\n".join(lines)


__all__ = [
    "get_mcp_context_prompt",
    "get_mcp_server_params",
    "get_mcp_status",
    "load_mcp_tools",
]
