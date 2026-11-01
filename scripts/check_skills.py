"""Self-check for the skill-based architecture (no Groq API or microphone needed).

Covers:
- SkillRegistry discovery and lazy SKILL.md loading
- load_skill_node general fallback (all tools, no escalation)
- safety_node runtime allowlist blocking
- safety_node skill escalation on top of global risk
- safety_node global HIGH risk still requires approval
"""

from langchain_core.messages import AIMessage

from app.agent.graph import (
    ALL_TOOL_NAMES,
    load_skill_node,
    registry,
    safety_node,
)
from app.safety.policy import RiskLevel


def make_state(tool_name=None, tool_args=None, skill_name="general",
               allowed_tools=None, require_approval_for=None):
    messages = []
    if tool_name:
        messages.append(AIMessage(
            content="",
            tool_calls=[{"name": tool_name, "args": tool_args or {}, "id": "1"}],
        ))
    return {
        "messages": messages,
        "skill_name": skill_name,
        "allowed_tools": allowed_tools,
        "require_approval_for": require_approval_for,
    }


# 1. Registry discovery
skills = {s.name for s in registry._skills.values()}
assert "file_organizer" in skills, skills
assert "project_setup" in skills, skills

# 2. load_skill_node general fallback
state = load_skill_node({"skill_name": "general"})
assert state["allowed_tools"] == list(ALL_TOOL_NAMES)
assert state["require_approval_for"] == []
assert state["skill_instructions"] == ""

# Unknown skill falls back to general
state = load_skill_node({"skill_name": "nope_such_skill"})
assert state["skill_name"] == "general"
assert state["allowed_tools"] == list(ALL_TOOL_NAMES)

# Real skill loads its SKILL.md instructions
state = load_skill_node({"skill_name": "file_organizer"})
assert state["skill_name"] == "file_organizer"
assert "create_folder" in state["allowed_tools"]
assert "create_folder" in state["require_approval_for"]
assert state["skill_instructions"], "SKILL.md should be loaded"

# 3. safety_node: runtime allowlist blocking
state = make_state(
    tool_name="create_folder",
    skill_name="file_organizer",
    allowed_tools=["find_file", "find_directory"],
)
result = safety_node(state)
assert result["risk_level"] == "blocked", result
assert "not allowed" in result["error"], result

# 4. safety_node: skill escalation (create_folder is MEDIUM globally, but skill
#    requires approval -> HITL)
state = make_state(
    tool_name="create_folder",
    skill_name="file_organizer",
    allowed_tools=["create_folder", "find_file"],
    require_approval_for=["create_folder"],
)
result = safety_node(state)
assert result["requires_approval"] is True, result
assert result["risk_level"] == RiskLevel.MEDIUM.value, result

# 5. safety_node: global HIGH risk still requires approval even if the skill
#    does not list it (global policy is authoritative)
state = make_state(
    tool_name="move_file",
    skill_name="file_organizer",
    allowed_tools=["move_file", "find_file"],
    require_approval_for=[],
)
result = safety_node(state)
assert result["requires_approval"] is True, result  # move_file is HIGH globally

# 6. safety_node: LOW risk auto-executes
state = make_state(
    tool_name="find_file",
    skill_name="file_organizer",
    allowed_tools=["find_file"],
    require_approval_for=[],
)
result = safety_node(state)
assert result["requires_approval"] is False, result
assert result["risk_level"] == RiskLevel.LOW.value, result

# 7. safety_node: message without tool calls -> neutral
state = {
    "messages": [AIMessage(content="hello", tool_calls=[])],
    "skill_name": "general",
    "allowed_tools": None,
    "require_approval_for": None,
}
result = safety_node(state)
assert result["pending_tool"] is None
assert result["risk_level"] is None

print("All skill-architecture self-checks passed.")
