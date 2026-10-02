from langchain_groq import ChatGroq

from forgeai.config.settings import settings
from forgeai.agent.state import AgentState
from forgeai.tools.file_ops import TOOLS

llm = ChatGroq(
    model = settings.model_name,
    temperature = settings.temperature,
    max_tokens = settings.max_tokens,
    api_key = settings.groq_api_key,
)

llm_with_tools = llm.bind_tools(TOOLS)

def agent_node(state: AgentState):
    """Call the LLM using the current conversation state."""

    response = llm_with_tools.invoke(
        state["messages"]
    )

    return{
        "messages": [response],
    }