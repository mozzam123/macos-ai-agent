from collections.abc import Callable

from pynput import keyboard
from app.config import HOTKEY


def listen_for_hotkey(callback: Callable[[], None]) -> None:
    """Listen continuously for the global macOS agent hotkey."""

    print(f"Agent ready. Press {HOTKEY} to activate.")

    with keyboard.GlobalHotKeys(
        {
            HOTKEY: callback,
        }
    ) as listener:
        listener.join()
