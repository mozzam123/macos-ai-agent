from dataclasses import dataclass
from pathlib import Path


@dataclass
class Skill:
    """A reusable workflow definition that guides the agent.

    Attributes:
        name: Unique skill identifier, matches its directory name.
        description: One-line summary shown in the planner catalogue.
        allowed_tools: Tool names the skill may invoke (runtime allowlist).
        require_approval_for: Tool names that need HITL approval on top of
            the global safety policy.
        instructions: Human-readable workflow from SKILL.md (loaded lazily).
        path: Skill directory on disk.
    """

    name: str
    description: str
    allowed_tools: list[str]
    require_approval_for: list[str]
    instructions: str = ""
    path: Path | None = None
