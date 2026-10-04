from typing import TypedDict


class AgentState(TypedDict):
    user_request: str
    action: str | None
    target: str | None
    result: str | None
    error: str | None
