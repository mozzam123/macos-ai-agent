from pathlib import Path


ALIASES = {
    "my dev folder": "~/Dev",
    "dev folder": "~/Dev",
    "desktop": "~/Desktop",
    "downloads": "~/Downloads",
    "documents": "~/Documents",
}


def resolve_alias(value: str) -> str | None:
    """Resolve a known user alias to an absolute path."""

    if not value:
        return None

    normalized = value.strip().lower()

    path = ALIASES.get(normalized)

    if not path:
        return None

    return str(Path(path).expanduser())
