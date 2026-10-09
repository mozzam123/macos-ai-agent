import subprocess
import webbrowser
from pathlib import Path
import shutil
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


@tool
def copy_file(source: str, destination: str) -> str:
    """Copy an existing file to another directory or file path.

    Use this when the user asks to copy or duplicate a file.
    """

    source_path = Path(source.strip()).expanduser()
    destination_path = Path(destination.strip()).expanduser()

    if not source_path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")

    if destination_path.is_dir():
        destination_path = destination_path / source_path.name

    if destination_path.exists():
        raise FileExistsError(f"Destination already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.copy2(source_path, destination_path)

    return f"Copied file to: {destination_path}"


@tool
def move_file(source: str, destination: str) -> str:
    """Move a file or directory to another directory/location.

    Do NOT use this for a simple rename.
    Use rename_path when only the name needs to change.
    """

    source_path = Path(source.strip()).expanduser()
    destination_path = Path(destination.strip()).expanduser()

    if not source_path.is_file():
        raise FileNotFoundError(f"Source file does not exist: {source_path}")

    if destination_path.is_dir():
        destination_path = destination_path / source_path.name

    if destination_path.exists():
        raise FileExistsError(f"Destination already exists: {destination_path}")

    destination_path.parent.mkdir(parents=True, exist_ok=True)

    shutil.move(str(source_path), str(destination_path))

    return f"Moved file to: {destination_path}"


@tool
def rename_path(path: str, new_name: str) -> str:
    """Rename an existing file or directory.

    Use this whenever the user asks to rename a file or folder.

    Do not use move_file for a simple rename.
    Use move_file only when moving something to another directory.
    """

    if not path or not path.strip():
        raise ValueError("Path cannot be empty.")

    if not new_name or not new_name.strip():
        raise ValueError("New name cannot be empty.")

    source = Path(path.strip()).expanduser()

    if not source.exists():
        raise FileNotFoundError(f"Path does not exist: {source}")

    destination = source.parent / new_name.strip()

    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    source.rename(destination)

    return f"Renamed: {source} → {destination}"


@tool
def create_file(file_path: str, content: str = "") -> str:
    """Create a new text file with optional content.

    Use this when the user asks to create a file.
    """

    path = Path(file_path.strip()).expanduser()

    if path.exists():
        raise FileExistsError(f"File already exists: {path}")

    path.parent.mkdir(parents=True, exist_ok=True)

    path.write_text(
        content,
        encoding="utf-8",
    )

    return f"Created file: {path}"


@tool
def open_in_cursor(path: str) -> str:
    """Open a file or folder in Cursor.

    Use this when the user specifically asks to open a project,
    folder, or file in Cursor.
    """

    target = Path(path.strip()).expanduser()

    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {target}")

    try:
        subprocess.run(
            ["open", "-a", "Cursor", str(target)],
            check=True,
            capture_output=True,
            text=True,
        )

        return f"Opened in Cursor: {target}"

    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or "Unknown macOS error."

        raise RuntimeError(f"Could not open '{target}' in Cursor: {error}") from exc


@tool
def initialize_git(directory: str) -> str:
    """Initialize a local Git repository inside an existing directory.

    Use this when the user asks to initialize Git or create a Git
    repository inside a folder.
    """

    path = Path(directory.strip()).expanduser()

    if not path.exists():
        raise FileNotFoundError(f"Directory does not exist: {path}")

    if not path.is_dir():
        raise ValueError(f"Path is not a directory: {path}")

    git_directory = path / ".git"

    if git_directory.exists():
        return f"Git is already initialized in: {path}"

    try:
        subprocess.run(
            ["git", "init", str(path)],
            check=True,
            capture_output=True,
            text=True,
        )

        return f"Initialized Git repository in: {path}"

    except subprocess.CalledProcessError as exc:
        error = exc.stderr.strip() or "Unknown Git error."

        raise RuntimeError(f"Could not initialize Git in '{path}': {error}") from exc


@tool
def find_directory(
    name: str,
    search_directory: str = "~",
) -> str:
    """Find a directory by name inside another directory.

    Use this when the user refers to a folder by name but its exact
    filesystem path is unknown.

    The search is case-insensitive and treats spaces, hyphens, and
    underscores as similar.

    Args:
        name: Folder name to search for.
        search_directory: Directory where the search should begin.
    """

    if not name or not name.strip():
        raise ValueError("Directory name cannot be empty.")

    root = Path(search_directory.strip()).expanduser()

    if not root.is_dir():
        raise FileNotFoundError(f"Search directory does not exist: {root}")

    def normalize(value: str) -> str:
        return value.lower().replace("-", "").replace("_", "").replace(" ", "")

    target = normalize(name)

    matches = []

    for path in root.rglob("*"):
        if not path.is_dir():
            continue

        if normalize(path.name) == target:
            matches.append(path)

    if not matches:
        return f"No directory named '{name}' found inside {root}."

    if len(matches) == 1:
        return str(matches[0])

    return "\n".join(str(path) for path in matches[:10])
