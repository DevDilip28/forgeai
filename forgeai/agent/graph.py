from langgraph.graph import START, END, StateGraph

from forgeai.agent.nodes import agent_node
from forgeai.agent.state import AgentState

def build_agent_graph():
    """Build a state graph for the agent."""

    graph = StateGraph(AgentState)

    graph.add_node("agent", agent_node)

    graph.add_edge(START, "agent")
    graph.add_edge("agent", END)

    return graph.compile()

agent_graph = build_agent_graph()
