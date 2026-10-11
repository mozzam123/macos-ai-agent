import json
from pathlib import Path


ALIASES_FILE = Path("aliases.json")


DEFAULT_ALIASES = {
    "my dev folder": "~/Dev",
    "dev folder": "~/Dev",
    "desktop": "~/Desktop",
    "downloads": "~/Downloads",
    "documents": "~/Documents",
}


def _load_aliases() -> dict[str, str]:
    if not ALIASES_FILE.exists():
        return DEFAULT_ALIASES.copy()

    try:
        data = json.loads(ALIASES_FILE.read_text())

        return {
            **DEFAULT_ALIASES,
            **data,
        }

    except (json.JSONDecodeError, OSError):
        return DEFAULT_ALIASES.copy()


def get_aliases() -> dict[str, str]:
    """Return all known aliases."""

    return _load_aliases()


def resolve_alias(
    value: str,
) -> str | None:
    """Resolve a known alias to an absolute path."""

    if not value:
        return None

    aliases = _load_aliases()

    normalized = value.strip().lower()

    path = aliases.get(normalized)

    if not path:
        return None

    return str(Path(path).expanduser())


def save_alias(
    alias: str,
    path: str,
) -> None:
    """Persist a user-defined alias."""

    aliases = _load_aliases()

    aliases[alias.strip().lower()] = path.strip()

    user_aliases = {
        key: value
        for key, value in aliases.items()
        if DEFAULT_ALIASES.get(key) != value or key not in DEFAULT_ALIASES
    }

    ALIASES_FILE.write_text(
        json.dumps(
            user_aliases,
            indent=2,
        )
    )
