import subprocess
import webbrowser
from pathlib import Path

from langchain_core.tools import tool


@tool
def open_application(app_name: str) -> str:
    """Open a macOS application by name.

    Use this when the user asks to open, launch, or start
    an application such as Finder, Safari, Cursor, or Notes.
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


@tool
def open_folder(folder_path: str) -> str:
    """Open an existing folder in macOS Finder.

    Use this when the user asks to open a folder or directory.
    The path may use ~ to represent the user's home directory.
    """
    if not folder_path or not folder_path.strip():
        raise ValueError("Folder path cannot be empty.")

    path = Path(folder_path.strip()).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Folder does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a folder: {path}")

    subprocess.run(
        ["open", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )

    return f"Opened folder: {path}"


@tool
def open_url(url: str) -> str:
    """Open a URL in the user's default web browser.

    Use this when the user asks to open or visit a website.
    """

    if not url or not url.strip():
        raise ValueError("URL cannot be empty.")

    url = url.strip()

    if not url.startswith(("http://", "https://")):
        url = f"https://{url}"

    webbrowser.open(url)

    return f"Opened URL: {url}"


@tool
def get_running_applications() -> str:
    """Return the names of currently running visible macOS applications.

    Use this when the user asks which applications are currently
    open or running.
    """

    script = """
    tell application "System Events"
        get name of every process whose background only is false
    end tell
    """

    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            check=True,
            capture_output=True,
            text=True,
        )

        applications = result.stdout.strip()

        return f"Running applications: {applications}"

    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or "Unknown AppleScript error."

        raise RuntimeError(f"Could not get running applications: {error}") from exc
