import shlex
import subprocess
from typing import Annotated

from langchain_core.tools import tool


@tool
async def execute_shell_command(
    command: Annotated[str, "Shell command to execute"],
    timeout: Annotated[int, "Timeout in seconds"] = 30,
) -> str:
    """Execute a shell command with safety checks and timeout."""
    try:
        dangerous_patterns = [
            "rm -rf /",
            ":(){ :|:& };:",
            "mkfs",
        ]

        if any(pattern in command for pattern in dangerous_patterns):
            return "Error: Command contains dangerous pattern and was blocked"

        result = subprocess.run(
            shlex.split(command),
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )

        output = []
        max_output = 2048

        if result.stdout:
            stdout = result.stdout

            if len(stdout) > max_output:
                stdout = f"{stdout[:max_output]}... (truncated)"

            output.append(f"STDOUT:\n{stdout}")

        if result.stderr:
            stderr = result.stderr

            if len(stderr) > max_output:
                stderr = f"{stderr[:max_output]}... (truncated)"

            output.append(f"STDERR:\n{stderr}")

        output.append(f"Exit Code: {result.returncode}")

        return "\n\n".join(output)

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds"

    except Exception as error:
        return f"Error executing command: {error!s}"


shell_tools = [execute_shell_command]


__all__ = [
    "execute_shell_command",
    "shell_tools",
]
