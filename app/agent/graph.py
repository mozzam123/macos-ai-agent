from langchain_ollama import ChatOllama

from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

from app.agent.state import AgentState
from app.tools.macos import (
    open_application,
    open_folder,
    open_url,
    get_running_applications,
)


tools = [
    open_application,
    open_folder,
    open_url,
    get_running_applications,
]


llm = ChatOllama(
    model="qwen3:8b",
    temperature=0,
)

llm_with_tools = llm.bind_tools(tools)


def agent_node(state: AgentState) -> dict:
    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}


def should_continue(state: AgentState) -> str:
    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("agent", agent_node)
    builder.add_node("tools", ToolNode(tools))

    builder.add_edge(START, "agent")

    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge("tools", "agent")

    return builder.compile()


graph = build_graph()
