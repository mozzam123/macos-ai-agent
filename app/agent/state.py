from typing import Annotated, TypedDict

from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]

    # Planning
    plan: list[str]

    # Execution
    current_step: int
    tool_results: list[str]
    error: str | None
    retry_count: int
    max_retries: int

    # Safety
    pending_tool: str | None
    pending_tool_args: dict | None
    risk_level: str | None
    approved: bool | None
    approved_action: dict | None
