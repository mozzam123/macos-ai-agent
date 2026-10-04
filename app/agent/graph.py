from langgraph.graph import StateGraph, START, END
from langchain_ollama import ChatOllama

from app.agent.state import AgentState
from app.agent.models import CommandIntent
from app.tools.macos import open_application


llm = ChatOllama(
    model="qwen3:8b",
    temperature=0,
    think=False,
)

command_model = llm.with_structured_output(CommandIntent)


def understand_command(state: AgentState) -> dict:
    """Use the local LLM to understand the user's command."""

    try:
        intent = command_model.invoke(
            f"""
You are the command interpreter for a macOS AI agent.

Currently the agent supports only one action:

open_application
- Opens a macOS application.
- target must contain the application name.

Examples:

User: Open Finder
action: open_application
target: Finder

User: Launch Cursor
action: open_application
target: Cursor

User: Start Safari
action: open_application
target: Safari

User request:
{state["user_request"]}
"""
        )

        return {
            "action": intent.action,
            "target": intent.target,
        }

    except Exception as exc:
        return {"error": f"Could not understand command: {exc}"}


def execute_action(state: AgentState) -> dict:
    """Execute the action selected by the agent."""

    if state.get("error"):
        return {}

    try:
        if state["action"] == "open_application":
            result = open_application(state["target"])

            return {"result": result}

        return {"error": f"Unsupported action: {state['action']}"}

    except Exception as exc:
        return {"error": str(exc)}


def build_graph():
    builder = StateGraph(AgentState)

    builder.add_node("understand_command", understand_command)
    builder.add_node("execute_action", execute_action)

    builder.add_edge(START, "understand_command")
    builder.add_edge("understand_command", "execute_action")
    builder.add_edge("execute_action", END)

    return builder.compile()


graph = build_graph()
