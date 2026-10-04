from pydantic import BaseModel, Field

from langchain_ollama import ChatOllama
from app.config import OLLAMA_MODEL
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode

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

llm = ChatOllama(
    model=OLLAMA_MODEL,
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
    """Create a high-level execution plan."""

    user_request = state["messages"][0].content

    plan = planner_llm.invoke(
        f"""
You are planning actions for a macOS AI agent.

Break the user's request into the smallest necessary ordered actions.

Rules:
- Do not invent actions.
- Do not invent filesystem paths.
- If a path is unknown, plan to find the directory or file first.
- Preserve the user's requested order of operations.

User request:
{user_request}
"""
    )

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
    """Execute the plan using available tools."""

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_results = state.get("tool_results", [])

    plan_text = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(plan))

    results_text = "\n".join(f"- {result}" for result in tool_results)

    system_message = f"""
You are a local macOS AI agent.

Complete the user's request using the available tools.

Execution plan:

{plan_text}

Current execution step:
{current_step + 1}

Previous successful tool results:

{results_text or "None"}

IMPORTANT EXECUTION RULES:

- Execute only ONE tool call at a time.
- Never request multiple tools in the same response.
- Wait for the result before deciding the next action.
- Follow the execution plan in order.
- Never invent filesystem paths.
- If a path is unknown, use a discovery tool.
- Use exact paths returned by tools.
- Do not repeat actions that already succeeded.
- Do not claim success unless the tool succeeded.

If all required actions are complete, return the final response
without calling another tool.
"""

    response = llm_with_tools.invoke(
        [
            ("system", system_message),
            *state["messages"],
        ]
    )

    return {"messages": [response]}


def track_tool_result(state: AgentState) -> dict:
    """Record the result of the latest tool execution."""

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
# Conditional routing
# ---------------------------------------------------------


def should_continue(state: AgentState) -> str:
    """Check whether the agent requested another tool."""

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "tools"

    return "end"


# ---------------------------------------------------------
# Build LangGraph
# ---------------------------------------------------------


def build_graph():
    builder = StateGraph(AgentState)

    # -------------------------
    # Nodes
    # -------------------------

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

    # -------------------------
    # Edges
    # -------------------------

    # 1. User request enters the planner
    builder.add_edge(
        START,
        "planner",
    )

    # 2. Planner creates the plan,
    #    then sends it to the agent
    builder.add_edge(
        "planner",
        "agent",
    )

    # 3. Agent either calls a tool or finishes
    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )

    # 4. After a tool executes,
    #    record its result in AgentState
    builder.add_edge(
        "tools",
        "track_tool_result",
    )

    # 5. Return to the agent so it can
    #    determine the next action
    builder.add_edge(
        "track_tool_result",
        "agent",
    )

    return builder.compile()


graph = build_graph()
