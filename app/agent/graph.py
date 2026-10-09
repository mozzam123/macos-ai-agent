import sqlite3

from pydantic import BaseModel, Field

from langchain_core.messages import ToolMessage
from langchain_groq import ChatGroq

from langgraph.checkpoint.sqlite import SqliteSaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt

from app.agent.prompts import AGENT_PROMPT, PLANNER_PROMPT
from app.agent.state import AgentState
from app.config import GROQ_MODEL
from app.safety.policy import RiskLevel, get_tool_risk
from app.tools.macos import (
    copy_file,
    create_file,
    create_folder,
    find_directory,
    find_file,
    get_running_applications,
    initialize_git,
    move_file,
    open_application,
    open_file,
    open_folder,
    open_in_cursor,
    open_url,
    rename_path,
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
    rename_path,
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
# Planner Schema
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
        # Retry state
        "retry_count": 0,
        "max_retries": 2,
        "execution_history": [],
        # Safety state
        "pending_tool": None,
        "pending_tool_args": None,
        "risk_level": None,
        "approved": None,
        "approved_action": None,
    }


# ---------------------------------------------------------
# Agent Node
# ---------------------------------------------------------


def agent_node(state: AgentState) -> dict:
    """Decide the next action."""

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


# ---------------------------------------------------------
# Safety Node
# ---------------------------------------------------------


def safety_node(state: AgentState) -> dict:
    """Inspect the requested tool and determine its risk."""

    last_message = state["messages"][-1]

    if not last_message.tool_calls:
        return {
            "pending_tool": None,
            "pending_tool_args": None,
            "risk_level": None,
        }

    # Only one tool call is allowed per agent turn.
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


# ---------------------------------------------------------
# Approval Node
# ---------------------------------------------------------


def approval_node(state: AgentState) -> dict:
    """Pause execution for a high-risk action."""

    tool_name = state.get("pending_tool")
    tool_args = state.get("pending_tool_args")
    risk_level = state.get("risk_level")

    decision = interrupt(
        {
            "type": "tool_approval",
            "tool": tool_name,
            "arguments": tool_args,
            "risk": risk_level,
            "message": (f"Approval required to execute " f"'{tool_name}'."),
        }
    )

    approved = bool(decision.get("approved", False))

    result = {
        "approved": approved,
    }

    if approved:
        result["approved_action"] = {
            "tool": tool_name,
            "args": tool_args,
        }

    return result


# ---------------------------------------------------------
# Rejection Node
# ---------------------------------------------------------


def rejection_node(state: AgentState) -> dict:
    """Record that the user rejected the action."""

    tool_name = state.get("pending_tool")
    tool_args = state.get("pending_tool_args")
    risk_level = state.get("risk_level")

    history = list(state.get("execution_history", []))

    history.append(
        {
            "tool": tool_name,
            "args": tool_args,
            "risk": risk_level,
            "status": "rejected",
            "result": "User rejected the action.",
        }
    )

    return {
        "error": (f"User rejected tool execution: " f"{tool_name}"),
        "execution_history": history,
        "pending_tool": None,
        "pending_tool_args": None,
        "risk_level": None,
        "approved": None,
    }


# ---------------------------------------------------------
# Tool Result Tracking
# ---------------------------------------------------------


def track_tool_result(state: AgentState) -> dict:
    """Track tool results, failures, retries, and execution history."""

    last_message = state["messages"][-1]
    result = str(last_message.content)

    tool_name = state.get("pending_tool")
    tool_args = state.get("pending_tool_args")
    risk_level = state.get("risk_level")

    history = list(state.get("execution_history", []))

    # Tool failed
    if isinstance(last_message, ToolMessage) and last_message.status == "error":
        history.append(
            {
                "tool": tool_name,
                "args": tool_args,
                "risk": risk_level,
                "status": "error",
                "result": result,
            }
        )

        return {
            "error": result,
            "retry_count": (state.get("retry_count", 0) + 1),
            "execution_history": history,
            "pending_tool": None,
            "pending_tool_args": None,
            "risk_level": None,
            "approved": None,
        }

    # Tool succeeded
    history.append(
        {
            "tool": tool_name,
            "args": tool_args,
            "risk": risk_level,
            "status": "success",
            "result": result,
        }
    )

    tool_results = [
        *state.get("tool_results", []),
        result,
    ]

    return {
        "tool_results": tool_results,
        "current_step": (state.get("current_step", 0) + 1),
        "error": None,
        "retry_count": 0,
        "execution_history": history,
        # Clear completed pending action
        "pending_tool": None,
        "pending_tool_args": None,
        "risk_level": None,
        "approved": None,
    }


# ---------------------------------------------------------
# Failure Node
# ---------------------------------------------------------


def failure_node(state: AgentState) -> dict:
    """Stop after too many failed recovery attempts."""

    error = state.get("error") or "Unknown tool error."

    return {
        "error": (
            "Execution stopped after too many "
            "failed recovery attempts. "
            f"Last error: {error}"
        )
    }


# ---------------------------------------------------------
# Routing
# ---------------------------------------------------------


def should_continue(state: AgentState) -> str:
    """Determine whether the agent requested a tool."""

    last_message = state["messages"][-1]

    if last_message.tool_calls:
        return "safety"

    return "end"


def route_after_safety(state: AgentState) -> str:
    """Route based on risk and previous approval."""

    risk = state.get("risk_level")

    # Low / medium actions execute automatically.
    if risk != RiskLevel.HIGH.value:
        return "execute"

    approved_action = state.get("approved_action")

    current_action = {
        "tool": state.get("pending_tool"),
        "args": state.get("pending_tool_args"),
    }

    # Exact same action was already approved
    # during this request.
    if approved_action == current_action:
        return "execute"

    return "high_risk"


def route_after_approval(state: AgentState) -> str:
    """Execute or reject the pending action."""

    if state.get("approved"):
        return "execute"

    return "reject"


def route_after_tool_result(
    state: AgentState,
) -> str:
    """Continue recovery or stop after retry limit."""

    retry_count = state.get(
        "retry_count",
        0,
    )

    max_retries = state.get(
        "max_retries",
        2,
    )

    # max_retries=2:
    #
    # failure 1 → recovery attempt
    # failure 2 → recovery attempt
    # failure 3 → stop
    if retry_count > max_retries:
        return "stop"

    return "continue"


# ---------------------------------------------------------
# Tool Error Handler
# ---------------------------------------------------------


def handle_tool_error(
    error: Exception,
) -> str:
    """Convert tool exceptions into agent-readable context."""

    return (
        "Tool execution failed.\n"
        f"Error: {str(error)}\n"
        "Review the error and decide the next "
        "appropriate action. "
        "Do not repeat the same failing action "
        "without changing something."
    )


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

    builder.add_node(
        "failure",
        failure_node,
    )

    # -----------------------------------------------------
    # START → Planner → Agent
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
    # Agent Routing
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
    # Safety Routing
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
    # Human Approval
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
    # Tool Execution + Retry Routing
    # -----------------------------------------------------

    builder.add_edge(
        "tools",
        "track_tool_result",
    )

    builder.add_conditional_edges(
        "track_tool_result",
        route_after_tool_result,
        {
            "continue": "agent",
            "stop": "failure",
        },
    )

    builder.add_edge(
        "failure",
        END,
    )

    # -----------------------------------------------------
    # SQLite Checkpointing
    # -----------------------------------------------------

    connection = sqlite3.connect(
        "checkpoints.db",
        check_same_thread=False,
    )

    checkpointer = SqliteSaver(connection)

    return builder.compile(
        checkpointer=checkpointer,
    )


graph = build_graph()
