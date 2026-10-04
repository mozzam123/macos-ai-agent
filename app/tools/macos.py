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


@tool
def create_folder(folder_path: str) -> str:
    """Create a new folder on the Mac.

    Use this when the user asks to create or make a folder/directory.
    The path may use ~ to represent the user's home directory.
    """

    if not folder_path or not folder_path.strip():
        raise ValueError("Folder path cannot be empty.")

    path = Path(folder_path.strip()).expanduser()

    if path.exists():
        if path.is_dir():
            return f"Folder already exists: {path}"

        raise FileExistsError(f"A file already exists at: {path}")

    path.mkdir(
        parents=True,
        exist_ok=False,
    )

    return f"Created folder: {path}"


@tool
def find_file(
    directory: str,
    extension: str | None = None,
    latest: bool = False,
) -> str:
    """Find a file inside a directory.

    Use this when the user asks to find or locate a file.

    Args:
        directory: Directory to search, such as ~/Downloads.
        extension: Optional file extension such as pdf, txt, or md.
        latest: If true, return the most recently modified matching file.
    """

    if not directory or not directory.strip():
        raise ValueError("Directory cannot be empty.")

    path = Path(directory.strip()).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    files = [file for file in path.iterdir() if file.is_file()]

    if extension:
        normalized_extension = extension.lower().lstrip(".")

        files = [
            file for file in files if file.suffix.lower() == f".{normalized_extension}"
        ]

    if not files:
        return "No matching files found."

    if latest:
        file = max(
            files,
            key=lambda item: item.stat().st_mtime,
        )

        return str(file)

    return "\n".join(str(file) for file in files)


@tool
def open_file(file_path: str) -> str:
    """Open an existing file using its default macOS application.

    Use this when the user asks to open a specific file.
    """

    if not file_path or not file_path.strip():
        raise ValueError("File path cannot be empty.")

    path = Path(file_path.strip()).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"File does not exist: {path}")

    if not path.is_file():
        raise ValueError(f"Path is not a file: {path}")

    subprocess.run(
        ["open", str(path)],
        check=True,
        capture_output=True,
        text=True,
    )

    return f"Opened file: {path}"
