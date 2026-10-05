from pydantic import BaseModel, Field

from langchain_ollama import ChatOllama
from app.config import OLLAMA_MODEL
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from app.config import GROQ_MODEL
from app.agent.prompts import AGENT_PROMPT, PLANNER_PROMPT

from app.agent.state import AgentState
from app.tools.macos import (
    open_application,
    open_folder,
    open_url,
    get_running_applications,
    create_folder,
    find_file,
    find_directory,
    open_file,
    copy_file,
    move_file,
    rename_file,
    create_file,
    open_in_cursor,
    initialize_git,
)


# ---------------------------------------------------------
# Tools
# ---------------------------------------------------------

tools = [
    open_application,
    open_folder,
    open_url,
    get_running_applications,
    create_folder,
    find_file,
    find_directory,
    open_file,
    copy_file,
    move_file,
    rename_file,
    create_file,
    open_in_cursor,
    initialize_git,
]


# ---------------------------------------------------------
# LLM
# ---------------------------------------------------------

llm = ChatGroq(
    model=GROQ_MODEL,
    temperature=0,
)

llm_with_tools = llm.bind_tools(tools)


# ---------------------------------------------------------
# Planner output
# ---------------------------------------------------------


class ExecutionPlan(BaseModel):
    steps: list[str] = Field(
        description="Ordered list of actions required to complete the request."
    )


planner_llm = llm.with_structured_output(ExecutionPlan)


# ---------------------------------------------------------
# Planner Node
# ---------------------------------------------------------


def planner_node(state: AgentState) -> dict:
    """Create the execution plan."""

    user_request = state["messages"][0].content

    prompt = PLANNER_PROMPT.format(
        user_request=user_request,
    )

    plan = planner_llm.invoke(prompt)

    return {
        "plan": plan.steps,
        "current_step": 0,
        "tool_results": [],
        "error": None,
    }


# ---------------------------------------------------------
# Agent Node
# ---------------------------------------------------------


def agent_node(state: AgentState) -> dict:
    """Decide and execute the next action."""

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_results = state.get("tool_results", [])

    plan_text = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(plan))

    results_text = "\n".join(f"- {result}" for result in tool_results)

    system_message = AGENT_PROMPT.format(
        plan=plan_text,
        current_step=current_step + 1,
        tool_results=results_text or "None",
    )

    response = llm_with_tools.invoke(
        [
            ("system", system_message),
            *state["messages"],
        ]
    )

    return {"messages": [response]}


def track_tool_result(state: AgentState) -> dict:
    """Store the latest successful tool result."""

    last_message = state["messages"][-1]

    result = str(last_message.content)

    tool_results = [
        *state.get("tool_results", []),
        result,
    ]

    return {
        "tool_results": tool_results,
        "current_step": state.get("current_step", 0) + 1,
    }


# ---------------------------------------------------------
# Routing
# ---------------------------------------------------------


def should_continue(state: AgentState) -> str:
    """Route to tools when the agent requests a tool."""

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node(
        "planner",
        planner_node,
    )

    builder.add_node(
        "agent",
        agent_node,
    )

    builder.add_node(
        "tools",
        ToolNode(tools),
    )

    builder.add_node(
        "track_tool_result",
        track_tool_result,
    )

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "agent",
    )

    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    builder.add_edge(
        "tools",
        "track_tool_result",
    )

    builder.add_edge(
        "track_tool_result",
        "agent",
    )

    return builder.compile()


graph = build_graph()
