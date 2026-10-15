import json
from app.config import RECENT_MEMORY_FILE
MAX_RECENT_ACTIONS = 10

# Only actions that preserve useful filesystem context survive app restarts.
CONTEXTUAL_TOOLS = frozenset(
    {
        "open_folder",
        "create_folder",
        "find_file",
        "find_directory",
        "open_file",
        "copy_file",
        "move_file",
        "rename_path",
        "create_file",
        "open_in_cursor",
        "initialize_git",
    }
)


def should_persist_action(action: dict) -> bool:
    """Return whether an action contains useful reusable path context."""

    if action.get("tool") not in CONTEXTUAL_TOOLS:
        return False

    return bool(action.get("path"))


def _clean_actions(actions: list[object]) -> list[dict]:
    """Discard malformed, low-value, and stale stored actions."""

    cleaned = [
        action
        for action in actions
        if isinstance(action, dict) and should_persist_action(action)
    ]

    return cleaned[-MAX_RECENT_ACTIONS:]


def load_recent_actions() -> list[dict]:
    """Load bounded, useful recent actions from local storage."""

    if not RECENT_MEMORY_FILE.exists():
        return []

    try:
        data = json.loads(RECENT_MEMORY_FILE.read_text())

        if not isinstance(data, list):
            return []

        actions = _clean_actions(data)

        if actions != data:
            save_recent_actions(actions)

        return actions

    except (json.JSONDecodeError, OSError):
        return []


def save_recent_actions(actions: list[dict]) -> None:
    """Persist only bounded, useful recent actions locally."""

    actions = _clean_actions(actions)

    RECENT_MEMORY_FILE.write_text(
        json.dumps(
            actions,
            indent=2,
        )
    )


def clear_recent_actions() -> None:
    """Remove all persisted recent-action memory."""

    if RECENT_MEMORY_FILE.exists():
        RECENT_MEMORY_FILE.unlink()
