from pydantic import BaseModel, Field
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langchain_groq import ChatGroq
from app.config import GROQ_MODEL
from app.agent.prompts import AGENT_PROMPT, PLANNER_PROMPT
from app.safety.policy import RiskLevel, get_tool_risk
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

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
        # Safety state
        "pending_tool": None,
        "pending_tool_args": None,
        "risk_level": None,
        "approved": None,
    }


# ---------------------------------------------------------
# Agent Node
# ---------------------------------------------------------


def agent_node(state: AgentState) -> dict:
    """Decide and execute the next action."""

    plan = state.get("plan", [])
    current_step = state.get("current_step", 0)
    tool_results = state.get("tool_results", [])
    error = state.get("error")

    plan_text = "\n".join(f"{index + 1}. {step}" for index, step in enumerate(plan))

    results_text = "\n".join(f"- {result}" for result in tool_results)

    system_message = AGENT_PROMPT.format(
        plan=plan_text,
        current_step=current_step + 1,
        tool_results=results_text or "None",
        error=error or "None",
    )

    response = llm_with_tools.invoke(
        [
            ("system", system_message),
            *state["messages"],
        ]
    )

    return {"messages": [response]}


def safety_node(state: AgentState) -> dict:
    """Inspect the requested tool and determine its risk level."""

    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return {
            "pending_tool": None,
            "pending_tool_args": None,
            "risk_level": None,
        }

    # We intentionally allow only one tool call per agent turn.
    tool_call = last_message.tool_calls[0]

    tool_name = tool_call["name"]
    tool_args = tool_call["args"]

    risk = get_tool_risk(tool_name)

    print(f"Safety check: {tool_name} " f"→ risk={risk.value}")

    return {
        "pending_tool": tool_name,
        "pending_tool_args": tool_args,
        "risk_level": risk.value,
    }


def approval_node(state: AgentState) -> dict:
    """Pause execution and request approval for a high-risk action."""

    tool_name = state.get("pending_tool")
    tool_args = state.get("pending_tool_args")
    risk_level = state.get("risk_level")

    decision = interrupt(
        {
            "type": "tool_approval",
            "tool": tool_name,
            "arguments": tool_args,
            "risk": risk_level,
            "message": f"Approval required to execute '{tool_name}'.",
        }
    )

    approved = bool(decision.get("approved", False))

    return {
        "approved": approved,
    }


def rejection_node(state: AgentState) -> dict:
    """Record that the user rejected the action."""

    tool_name = state.get("pending_tool")

    return {
        "error": f"User rejected tool execution: {tool_name}",
        "pending_tool": None,
        "pending_tool_args": None,
        "risk_level": None,
        "approved": None,
    }


def track_tool_result(state: AgentState) -> dict:
    """Track successful tool results and tool errors."""

    last_message = state["messages"][-1]
    result = str(last_message.content)

    # ToolNode marks handled failures with error status
    if isinstance(last_message, ToolMessage) and last_message.status == "error":
        return {
            "error": result,
        }

    tool_results = [
        *state.get("tool_results", []),
        result,
    ]

    return {
        "tool_results": tool_results,
        "current_step": state.get("current_step", 0) + 1,
        "error": None,
    }


# ---------------------------------------------------------
# Routing
# ---------------------------------------------------------


def should_continue(state: AgentState) -> str:
    """Determine whether the agent wants to execute a tool."""

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "safety"

    return "end"


def route_after_safety(state: AgentState) -> str:
    """Route based on the requested tool's risk level."""

    risk = state.get("risk_level")

    if risk == RiskLevel.HIGH.value:
        return "high_risk"

    return "execute"


def handle_tool_error(error: Exception) -> str:
    """Convert tool exceptions into information the agent can reason about."""

    return (
        "Tool execution failed.\n"
        f"Error: {str(error)}\n"
        "Review the error and decide the next appropriate action. "
        "Do not repeat the same failing action without changing something."
    )


def route_after_approval(state: AgentState) -> str:
    """Execute or reject the pending action."""

    if state.get("approved"):
        return "execute"

    return "reject"


# ---------------------------------------------------------
# Graph
# ---------------------------------------------------------


def build_graph():
    builder = StateGraph(AgentState)

    # -----------------------------------------------------
    # Nodes
    # -----------------------------------------------------

    builder.add_node(
        "planner",
        planner_node,
    )

    builder.add_node(
        "agent",
        agent_node,
    )

    builder.add_node(
        "safety",
        safety_node,
    )

    builder.add_node(
        "approval",
        approval_node,
    )

    builder.add_node(
        "rejection",
        rejection_node,
    )

    builder.add_node(
        "tools",
        ToolNode(
            tools,
            handle_tool_errors=handle_tool_error,
        ),
    )

    builder.add_node(
        "track_tool_result",
        track_tool_result,
    )

    # -----------------------------------------------------
    # Start
    # -----------------------------------------------------

    builder.add_edge(
        START,
        "planner",
    )

    builder.add_edge(
        "planner",
        "agent",
    )

    # -----------------------------------------------------
    # Agent → Safety
    # -----------------------------------------------------

    builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "safety": "safety",
            "end": END,
        },
    )

    # -----------------------------------------------------
    # Safety
    # -----------------------------------------------------

    builder.add_conditional_edges(
        "safety",
        route_after_safety,
        {
            "execute": "tools",
            "high_risk": "approval",
        },
    )

    # -----------------------------------------------------
    # Human approval
    # -----------------------------------------------------

    builder.add_conditional_edges(
        "approval",
        route_after_approval,
        {
            "execute": "tools",
            "reject": "rejection",
        },
    )

    builder.add_edge(
        "rejection",
        END,
    )

    # -----------------------------------------------------
    # Tool execution
    # -----------------------------------------------------

    builder.add_edge(
        "tools",
        "track_tool_result",
    )

    builder.add_edge(
        "track_tool_result",
        "agent",
    )

    # -----------------------------------------------------
    # Checkpointing
    # -----------------------------------------------------

    checkpointer = InMemorySaver()

    return builder.compile(
        checkpointer=checkpointer,
    )


graph = build_graph()
