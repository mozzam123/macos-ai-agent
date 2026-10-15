from collections.abc import Callable

from pynput import keyboard

from app.config import HOTKEY


def start_hotkey_listener(
    callback: Callable[[], None],
) -> keyboard.GlobalHotKeys:
    """Start the global hotkey listener without blocking."""

    listener = keyboard.GlobalHotKeys(
        {
            HOTKEY: callback,
        }
    )

    listener.start()

    print(f"Agent ready. Press {HOTKEY} to activate.")

    return listener
