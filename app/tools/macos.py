import subprocess

from langchain_core.tools import tool


@tool
def open_application(app_name: str) -> str:
    """Open a macOS application by its name.

    Use this when the user asks to open, launch, or start
    an application on macOS.
    """
    if not app_name or not app_name.strip():
        raise ValueError("Application name cannot be empty.")

    app_name = app_name.strip()

    try:
        subprocess.run(
            ["open", "-a", app_name],
            check=True,
            capture_output=True,
            text=True,
        )

        return f"Opened {app_name}."

    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or "Unknown macOS error."

        raise RuntimeError(f"Could not open application '{app_name}': {error}") from exc
