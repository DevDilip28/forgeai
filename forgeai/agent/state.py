from typing import Annotated, NotRequired, TypedDict

from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[BaseMessage], add_messages]

    iteration_count: NotRequired[int]
    working_directory: NotRequired[str]

    tool_calls_made: NotRequired[list[str]]
    files_modified: NotRequired[list[str]]

    pending_approval: NotRequired[bool]
    approval_granted: NotRequired[bool]

    current_mode: NotRequired[str]
    mode_switch_pending: NotRequired[dict[str, str]]
