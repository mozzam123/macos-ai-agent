import json
from pathlib import Path


RECENT_MEMORY_FILE = Path("recent_memory.json")
MAX_RECENT_ACTIONS = 10


def load_recent_actions() -> list[dict]:
    """Load recent successful actions from local storage."""

    if not RECENT_MEMORY_FILE.exists():
        return []

    try:
        data = json.loads(RECENT_MEMORY_FILE.read_text())

        if not isinstance(data, list):
            return []

        return data[-MAX_RECENT_ACTIONS:]

    except (json.JSONDecodeError, OSError):
        return []


def save_recent_actions(
    actions: list[dict],
) -> None:
    """Persist recent successful actions locally."""

    actions = actions[-MAX_RECENT_ACTIONS:]

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
