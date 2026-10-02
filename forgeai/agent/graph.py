from langgraph.graph import START, END, StateGraph
from langgraph.prebuilt import ToolNode, tools_condition

from forgeai.agent.nodes import agent_node
from forgeai.agent.state import AgentState
from forgeai.tools.file_ops import TOOLS


def build_agent_graph():
    """Build a state graph for the agent."""

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    graph.add_node("tools", ToolNode(TOOLS))

    graph.add_edge(START, "agent")
    graph.add_conditional_edges("agent", tools_condition)
    graph.add_edge("tools", "agent")

    return graph.compile()


agent_graph = build_agent_graph()
