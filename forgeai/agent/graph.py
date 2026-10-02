from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Any

from langchain_groq import ChatGroq
from langgraph.graph import END, StateGraph
from langgraph.prebuilt import ToolNode

from forgeai.agent.nodes import approval_node, create_agent_node, should_continue
from forgeai.agent.state import AgentState
from forgeai.config.settings import settings
from forgeai.tools import all_tools
from forgeai.tools.mcp import get_mcp_context_prompt, load_mcp_tools


@asynccontextmanager
async def create_agent_graph(
    checkpointer: Any | None = None,
) -> AsyncIterator[Any]:
    llm = ChatGroq(
        model=settings.model_name,
        temperature=settings.temperature,
        api_key=settings.groq_api_key,
        max_tokens=settings.max_tokens,
    )

    async with load_mcp_tools() as mcp_tools:
        all_available_tools = all_tools + mcp_tools
        mcp_context = get_mcp_context_prompt()

        agent_node = create_agent_node(
            llm,
            all_tools,
            mcp_tools,
            mcp_context=mcp_context,
        )

        tool_node = ToolNode(all_available_tools)

        workflow = StateGraph(AgentState)

        workflow.add_node("agent", agent_node)
        workflow.add_node("tools", tool_node)

        if settings.approval_required:
            workflow.add_node("approval", approval_node)

        workflow.set_entry_point("agent")

        workflow.add_conditional_edges(
            "agent",
            should_continue,
            {
                "continue": "tools",
                "request_approval": (
                    "approval" if settings.approval_required else "tools"
                ),
                "end": END,
            },
        )

        workflow.add_edge("tools", "agent")

        if settings.approval_required:
            workflow.add_conditional_edges(
                "approval",
                lambda state: ("tools" if state.get("approval_granted") else END),
            )

        yield workflow.compile(checkpointer=checkpointer)


__all__ = ["create_agent_graph"]
