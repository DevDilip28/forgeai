from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class AgentMode(Enum):
    CODE = "CODE"
    ARCHITECT = "ARCHITECT"
    ASK = "ASK"


@dataclass
class ModeConfig:
    mode: AgentMode
    name: str
    description: str
    allows_file_write: bool
    allows_shell_exec: bool
    restricted_to_plans_dir: bool


CODE_MODE = ModeConfig(
    mode=AgentMode.CODE,
    name="CODE",
    description="Full access mode",
    allows_file_write=True,
    allows_shell_exec=True,
    restricted_to_plans_dir=False,
)

ARCHITECT_MODE = ModeConfig(
    mode=AgentMode.ARCHITECT,
    name="ARCHITECT",
    description="Planning mode - file operations restricted to .forgeai/plans/",
    allows_file_write=True,
    allows_shell_exec=True,
    restricted_to_plans_dir=True,
)

ASK_MODE = ModeConfig(
    mode=AgentMode.ASK,
    name="ASK",
    description="Conversation mode - no file writes or shell execution",
    allows_file_write=False,
    allows_shell_exec=False,
    restricted_to_plans_dir=False,
)


_MODE_CONFIGS = {
    AgentMode.CODE: CODE_MODE,
    AgentMode.ARCHITECT: ARCHITECT_MODE,
    AgentMode.ASK: ASK_MODE,
}


def get_mode_config(mode: AgentMode) -> ModeConfig:
    return _MODE_CONFIGS[mode]


def is_tool_allowed(tool_name: str, mode: AgentMode) -> bool:
    config = get_mode_config(mode)

    if tool_name == "write_file":
        return config.allows_file_write

    if tool_name == "execute_shell_command":
        return config.allows_shell_exec

    return True


def validate_file_path(
    path: str,
    mode: AgentMode,
    plans_dir: Path,
) -> tuple[bool, str]:
    config = get_mode_config(mode)

    if not config.restricted_to_plans_dir:
        return True, ""

    if not is_path_in_plans_dir(path, plans_dir):
        return (
            False,
            f"ARCHITECT mode restricts file operations to "
            f"{plans_dir}. Switch to CODE mode for unrestricted access.",
        )

    return True, ""


def is_path_in_plans_dir(
    path: str,
    plans_dir: Path,
) -> bool:
    try:
        resolved_path = Path(path).resolve()
        resolved_plans = plans_dir.resolve()

        return resolved_path.is_relative_to(resolved_plans)

    except (ValueError, OSError):
        return False
