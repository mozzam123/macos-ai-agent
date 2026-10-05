from enum import Enum


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


TOOL_RISK_LEVELS = {
    # Read / open operations
    "open_application": RiskLevel.LOW,
    "open_folder": RiskLevel.LOW,
    "open_url": RiskLevel.LOW,
    "get_running_applications": RiskLevel.LOW,
    "find_file": RiskLevel.LOW,
    "find_directory": RiskLevel.LOW,
    "open_file": RiskLevel.LOW,
    "open_in_cursor": RiskLevel.LOW,
    # Create / copy operations
    "create_folder": RiskLevel.MEDIUM,
    "create_file": RiskLevel.MEDIUM,
    "copy_file": RiskLevel.MEDIUM,
    "initialize_git": RiskLevel.MEDIUM,
    # Existing data is modified
    "move_file": RiskLevel.HIGH,
    "rename_file": RiskLevel.HIGH,
}


def get_tool_risk(tool_name: str) -> RiskLevel:
    """Return the configured risk level for a tool."""

    return TOOL_RISK_LEVELS.get(
        tool_name,
        RiskLevel.HIGH,
    )
